# pdns_exporter

A Python-based Prometheus exporter for monitoring **PowerDNS** health and availability. It continuously tests DNS resolution (read) and A record creation/deletion (write) against PowerDNS servers, exposes the results as Prometheus metrics, and computes 24-hour availability by querying historical data from Grafana.

---

## How It Works

The exporter runs four background threads, each on its own collection interval:

| Thread | Role | Mode | What it does |
|---|---|---|---|
| `pdns-read-status-thread` | secondary | status | Resolves a test FQDN via Miremad and Vanak DNS servers |
| `pdns-write-status-thread` | primary | status | Creates and deletes a temporary A record via the PowerDNS API |
| `pdns-read-availability-thread` | secondary | availability | Queries Grafana for 24h read-status history and computes uptime % |
| `pdns-write-availability-thread` | primary | availability | Queries Grafana for 24h write-status history and computes uptime % |

Metrics are exposed over a WSGI endpoint (`/metrics`) served by **Gunicorn**.

---

## Requirements

- Docker
- Docker Compose
- A running Prometheus instance
- A running Grafana instance with a Prometheus datasource configured
- PowerDNS primary and secondary nodes

---

## Deployment

### 1. Configure environment variables

Create a `.env` file in the same directory as `docker-compose.yml`:

```env
PDNS_ADDR=http://pdns.example.com:8081
PDNS_TOKEN=your-pdns-api-key
PDNS_WRITE_RECORD=test.example.com
PDNS_QUERY_RECORD=query.example.com

ME_DNS=10.0.0.1
VNK_DNS=10.0.0.2

GRAFANA_ADDR=http://grafana.example.com:3000
GRAFANA_TOKEN=your-grafana-service-account-token
GRAFANA_PROM_DS=your-prometheus-datasource-uid

READ_STATUS_PROMQL=pdns_read_current_status
WRITE_STATUS_PROMQL=pdns_write_current_status

READ_STATUS_COLLECTION_INTERVAL=1
READ_AVAILABILITY_COLLECTION_INTERVAL=1440
WRITE_STATUS_COLLECTION_INTERVAL=15
WRITE_AVAILABILITY_COLLECTION_INTERVAL=1440
```

### 2. Use the compose file and Start the container
```docker-compose.yml
services:
  powerdns-exporter:
    image: sinazare/powerdns-exporter:1.0

    ports:
      - "5335:5335"

    env_file:
      - .env

    restart: unless-stopped

```

```bash
docker compose up -d
```

Metrics will be available at:

```
http://<host>:5335/metrics
```

---

## Environment Variables

All variables are required unless a default is noted.

| Variable | Description | Default |
|---|---|---|
| `PDNS_ADDR` | PowerDNS API base URL (e.g. `http://pdns.example.com:8081`) | — |
| `PDNS_TOKEN` | PowerDNS API key (`X-API-Key`) | — |
| `PDNS_WRITE_RECORD` | FQDN used for the write test (e.g. `test.example.com`) | — |
| `PDNS_QUERY_RECORD` | FQDN used for the read/resolution test | — |
| `ME_DNS` | Comma-separated IP(s) of the Miremad DNS server (Datacenter #1 Secondary) | — |
| `VNK_DNS` | Comma-separated IP(s) of the Vanak DNS server (Datacenter #2 Secondary) | — |
| `GRAFANA_ADDR` | Grafana base URL (e.g. `http://grafana.example.com:3000`) | — |
| `GRAFANA_TOKEN` | Grafana service account token | — |
| `GRAFANA_PROM_DS` | UID of the Prometheus datasource in Grafana (used for PromQL queries) | — |
| `READ_STATUS_PROMQL` | PromQL metric name for read status history | `pdns_read_current_status` |
| `WRITE_STATUS_PROMQL` | PromQL metric name for write status history | `pdns_write_current_status` |
| `READ_STATUS_COLLECTION_INTERVAL` | How often (in minutes) to test DNS name resolution | `1` |
| `READ_AVAILABILITY_COLLECTION_INTERVAL` | How often (in minutes) to compute read availability; also the Grafana lookback window | `1440` (24h) |
| `WRITE_STATUS_COLLECTION_INTERVAL` | How often (in minutes) to test A record creation/deletion | `15` |
| `WRITE_AVAILABILITY_COLLECTION_INTERVAL` | How often (in minutes) to compute write availability; also the Grafana lookback window | `1440` (24h) |

---

## Prometheus Integration

### Scrape config

Add the following to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "powerdns-exporter"
    static_configs:
      - targets:
          - localhost:5335
```

### Alerting rules

```yaml
groups:
  - name: PowerDNS-Exporter-Alerts
    rules:

      - alert: PowerDNSExporterJobDown
        expr: up{job='powerdns-exporter'} == 0
        labels:
          severity: critical
          team: sysops
          type: prod
          channel: sms
        annotations:
          summary: Job powerdns-exporter Failed
          description: |
            Scrape failed for job

            Instance:   {{ $labels.instance }}

      - alert: PowerDNSAvailabilityFewSamplesCollected
        expr: |
          pdns_24h_availability_samples_total < 1440
        labels:
          severity: critical
          team: sysops
          type: prod
          channel: sms
        annotations:
          summary: powerdns-exporter collected few samples
          description: |
            powerdns-exporter collected fewer samples than expected

            Role:       {{ $labels.role }}
            Function:   {{ $labels.func }}
            Date:       {{ $labels.date }}
            Samples:    {{ printf "%.0f" $value }}

      - alert: PowerDNSExporterSlowCollection
        expr: pdns_exporter_last_collection_duration_seconds > 60
        labels:
          severity: critical
          team: sysops
          type: prod
          channel: sms
        annotations:
          summary: powerdns-exporter collection slow
          description: |
            powerdns-exporter took more than 1 minute to collect latest data

            Role:                 {{ $labels.role }}
            Mode:                 {{ $labels.mode }}
            Collection Interval:  {{ $labels.collection_interval }}
            Value:                {{ printf "%.0f" $value }}

      - alert: PowerDNSExporterCollectionFailure
        expr: pdns_exporter_last_collection_success == 0
        labels:
          severity: critical
          team: sysops
          type: prod
          channel: sms
        annotations:
          summary: powerdns-exporter collection failed
          description: |
            powerdns-exporter failed to collect latest data

            Role:                 {{ $labels.role }}
            Mode:                 {{ $labels.mode }}
            Collection Interval:  {{ $labels.collection_interval }}
            Last Error:           {{ $labels.last_error }}
```

> **Note on sample thresholds:** The `PowerDNSAvailabilityFewSamplesCollected` alert expects `primary` to have at least 96 samples (one per `WRITE_STATUS_COLLECTION_INTERVAL=15m` over 24h) and `secondary` to have at least 1440 (one per `READ_STATUS_COLLECTION_INTERVAL=1m` over 24h). Adjust these thresholds if you change the collection intervals.

---

## Exposed Metrics

### App Metrics

| Metric | Labels | Description |
|---|---|---|
| `pdns_read_current_status` | `role`, `miremad`, `vanak` | DNS resolution status: `-1`=no data, `0`=both secondaries down, `1`=at least one secondary dns up |
| `pdns_write_current_status` | `role`, `datacenter` | A record creation status (calculations done against primary dns): `-1`=no data, `0`=down, `1`=up |
| `pdns_24h_availability_percent` | `role`, `func`, `date` | Availability % over the last 24h (`-1` if data unavailable) |
| `pdns_24h_availability_samples_total` | `role`, `func`, `date` | Total samples in the 24h window |
| `pdns_24h_availability_samples_up` | `role`, `func`, `date` | Number of "up" samples in the 24h window |

### Exporter Self-Metrics

| Metric | Labels | Description |
|---|---|---|
| `pdns_exporter_last_collection_success` | `role`, `mode`, `collection_interval`, `last_error` | `1` if the last collection succeeded, `0` otherwise |
| `pdns_exporter_last_collection_duration_seconds` | `role`, `mode`, `collection_interval` | Duration of the last collection in seconds |
| `pdns_exporter_collection_errors_total` | `role`, `mode`, `collection_interval` | Cumulative collection error count |

#### `pdns_read_current_status` value reference

| Value | Meaning |
|---|---|
| `1` | At least one DNS server resolved successfully |
| `0` | Both Datacenter#1 and Datacenter#2 resolvers failed |
| `-1` | No data (resolver returned `None`) |

---

## Write Test Logic

For each write-status collection, the exporter:

1. Generates a unique record name by appending a Unix timestamp to the configured `PDNS_WRITE_RECORD` subdomain (e.g. `test-1718000000.example.com.`)
2. Creates an A record pointing to `127.0.0.127` via the PowerDNS HTTP API (`PATCH /api/v1/servers/localhost/zones/{zone}`)
3. Immediately deletes the record
4. Reports success or failure

---

## Retry Behaviour

DNS resolution and Grafana queries use an exponential-backoff retry helper:

- **Max attempts:** 2 (status collectors) / 5 (availability collectors)
- **Initial delay:** 2 seconds
- **Backoff factor:** ×2 per attempt

---

## Concurrency

A single `threading.Lock` (`collection_lock`) serialises all collector writes and the `/metrics` scrape read, preventing partial metric state from being exposed during a collection cycle.
