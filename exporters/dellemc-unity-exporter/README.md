# Dell EMC Unity Prometheus Exporter

A lightweight Prometheus exporter for collecting CPU utilization metrics from Dell EMC Unity storage arrays using the Unity REST API.

The exporter follows the **multi-target exporter pattern**, similar to the Prometheus Blackbox Exporter. A single exporter instance can scrape multiple Unity arrays by passing the target as a query parameter.

---

## Features

* Collects Unity Storage Processor (SP) CPU utilization
* Supports both SPA and SPB metrics
* Multi-target architecture
* Dockerized deployment
* Health endpoint
* Prometheus-compatible metrics output
* Basic authentication against Unity REST API

---

## Exported Metrics

### CPU Utilization

| Metric                                  | Description                                       | Labels         |
| --------------------------------------- | ------------------------------------------------- | -------------- |
| `dellemc_unity_cpu_utilization_percent` | CPU utilization percentage of a Storage Processor | `target`, `sp` |

Example:

```text
dellemc_unity_cpu_utilization_percent{target="vra-unity480-g1u19.company.com",sp="spa"} 12.3
dellemc_unity_cpu_utilization_percent{target="vra-unity480-g1u19.company.com",sp="spb"} 14.1
```

---

### Exporter Health

| Metric             | Description                                     | Labels              |
| ------------------ | ----------------------------------------------- | ------------------- |
| `dellemc_unity_up` | Unity target availability status (1=up, 0=down) | `target`, `problem` |

Example:

```text
dellemc_unity_up{target="vra-unity480-g1u19.company.com",problem="none"} 1
```

Failure example:

```text
dellemc_unity_up{target="vra-unity480-g1u19.company.com",problem="failed to get response from url with status 401"} 0
```

---

## Architecture

```text
Prometheus
    |
    | target=<unity-array>
    v
Dell EMC Unity Exporter
    |
    | REST API
    v
Dell EMC Unity Storage
```

The exporter receives the Unity hostname through the `target` query parameter:

```text
http://exporter:9105/metrics?target=unity480.company.com
```

---

## Requirements

* Dell EMC Unity array with REST API access enabled
* Read-only monitoring account (recommended)
* Docker and Docker Compose

---

## Environment Variables

Create a `.env` file:

```env
UNITY_USERNAME=monitoring-user
UNITY_PASSWORD=your-password
```

| Variable         | Description             |
| ---------------- | ----------------------- |
| `UNITY_USERNAME` | Unity REST API username |
| `UNITY_PASSWORD` | Unity REST API password |

---

## Docker Deployment

### docker-compose.yml

```yaml
services:
  dellemc-unity-exporter:
    image: sinazare/dellemc-unity-exporter:1.0
    container_name: dellemc-unity-exporter
    ports:
      - "9105:9105"
    env_file:
      - .env
    restart: unless-stopped
```

### Start Exporter

```bash
docker compose up -d
```

Verify:

```bash
docker ps
```

---

## Endpoints

### Health Check

```http
GET /health
```

Example:

```bash
curl http://localhost:9105/health
```

Response:

```text
OK
```

---

### Metrics Endpoint

```http
GET /metrics?target=<unity-hostname>
```

Example:

```bash
curl "http://localhost:9105/metrics?target=unity480.company.com"
```

---

## Prometheus Configuration

Example scrape configuration:

```yaml
scrape_configs:
  - job_name: dellemc-unity
    metrics_path: /metrics

    static_configs:
      - targets:
        - unity480.company.com
        - unity680.company.com
        - unity400bck.company.com

        labels:
          team: storage
          subteam: storage_san

    relabel_configs:
      # Pass Unity hostname as query parameter
      - source_labels: [__address__]
        target_label: __param_target

      # Preserve original hostname as instance label
      - source_labels: [__address__]
        target_label: instance

      # Replace scrape destination with exporter
      - target_label: __address__
        replacement: localhost:9105
```

---

### Alert Rules
Example Prometheus alert rule configuration:
```yml
groups:
- name: unity_alerts
  rules:

  ## UP ##
  - alert: UnityScrapeFailed
    expr: up{job='dellemc-unity'} != 1
    for: 5m
    labels:
      severity: critical
      channel: sms
      team: storage
      subteam: storage_san
      type: prod
    annotations:
      summary: "Unity Metric Collection Failed in {{ $labels.job }} job"
      description: |
        Instance:     {{ $labels.instance }}
        Job:          {{ $labels.job }}
        Value:        {{ $value }}


  ## Up Service Based ##
  - alert: UnityDataGatheringFailed
    expr: dellemc_unity_up != 1
    for: 5m
    labels:
      severity: critical
      type: prod
      channel: sms
      team: storage
      subteam: storage_san
    annotations:
      summary: "Unity Data Gathering Failed on {{ $labels.target }}"
      description: |
        Target:     {{ $labels.target }}
        Problem:    {{ $labels.problem }}


  ## CPU ##
  - alert: UnityCPUUsageVeryHigh
    expr: dellemc_unity_cpu_utilization_percent > 90
    for: 5m
    labels:
      severity: critical
      channel: sms
      team: storage
      subteam: storage_san
      type: prod
    annotations:
      summary: Unity Node {{ $labels.target }} SP {{ $labels.sp }} CPU Usage Over 90%
      description: |
        Node:    {{ $labels.target }}
        SP:      {{ $labels.sp }}
        Value:   {{ printf "%.2f" $value }}%

  - alert: UnityCPUUsageHigh
    expr: dellemc_unity_cpu_utilization_percent > 80
    for: 5m
    labels:
      severity: warning
      team: storage
      subteam: storage_san
      type: prod
    annotations:
      summary: Unity Node {{ $labels.target }} SP {{ $labels.sp }} CPU Usage Over 80%
      description: |
        Node:    {{ $labels.target }}
        SP:      {{ $labels.sp }}
        Value:   {{ printf "%.2f" $value }}%
```
---

## Testing

### Verify Unity API Connectivity

```bash
curl -k -u USERNAME:PASSWORD \
https://UNITY_HOST/api/types/metricValue/instances?filter=path%20EQ%20%22sp.*.cpu.summary.utilization%22&per_page=1
```

Expected result:

```json
{
  "entries": [
    {
      "content": {
        "values": {
          "spa": 10.4,
          "spb": 12.8
        }
      }
    }
  ]
}
```

### Verify Exporter

```bash
curl "http://localhost:9105/metrics?target=UNITY_HOST"
```

---

## Troubleshooting

### Missing Target Parameter

Response:

```text
Missing target parameter
```

Example of correct usage:

```bash
curl "http://localhost:9105/metrics?target=unity480.company.com"
```

---

### Authentication Failure

Check:

* `UNITY_USERNAME`
* `UNITY_PASSWORD`
* Unity user permissions

Metric:

```text
dellemc_unity_up{problem="failed to get response from url with status 401"} 0
```

---

### Connectivity Issues

Possible causes:

* DNS resolution failure
* Firewall restrictions
* Unity REST API unavailable
* TLS connectivity issues

Inspect the `problem` label in the `dellemc_unity_up` metric for details.

---

## Security Notes

* HTTPS certificate validation is currently disabled (`verify=False`).
* Deploy only within trusted internal networks.
* Use a dedicated read-only monitoring account.
* Restrict access to the exporter endpoint using firewall rules or reverse proxy controls.

---

## License

Internal / private project.
