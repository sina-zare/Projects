# Cisco Nexus VPC Prometheus Exporter

A multi-target Prometheus exporter that polls Cisco Nexus 9000 switches over SSH
(via [netmiko](https://github.com/ktbyers/netmiko)) and exposes VPC (Virtual
Port Channel) health metrics, peer link status, peer keepalive status,
consistency checks, and port-channel health.

Built for pairs of Nexus 9000 switches running VPC domains, to catch
degraded peer links, consistency mismatches, or dual-active risk before they
cause an outage.

## How it works

- The exporter is a WSGI app (served by gunicorn) exposing `GET /metrics?target=<switch-host>`.
- On each scrape, it runs `sh vpc brief | json` and `show vpc peer-keepalive | json`
  against the target switch over SSH and parses the output into Prometheus gauges.
- SSH sessions are **pooled per target host and reused across scrapes** a new
  session is only opened the first time a host is seen, or if the existing
  session has actually died. A per-host lock serializes concurrent scrapes of
  the same switch while different switches scrape independently.
- On a failed command run, the session is dropped and retried exactly once
  with a fresh connection (handles switch reboots, cleared vtys, etc.)
  without paying the reconnect cost on every healthy scrape.
- A `GET /health` endpoint reports the current pool state (how many sessions
  are alive/dead, per host).


## Metrics exposed

| Metric | Labels | Meaning |
|---|---|---|
| `nxos_vpc_scrape_up` | `name` | 1 if the scrape of this target succeeded |
| `nxos_vpc_scrape_duration_seconds` | `name` | Time spent collecting metrics for this target |
| `nxos_vpc_peer_link_health` | `name, neighbor, reason, domain_id, role, vrf, state, type1_consistency, per_vlan_peer_consistency, type2_consistency` | 1 if VPC peer link is healthy (`peer-ok`), else 0 |
| `nxos_vpc_peer_keepalive_health` | `name, neighbor, domain_id, role, vrf, state` | 1 if the peer-keepalive link is up (`peer-alive`), else 0 |
| `nxos_vpc_uptime` | `name, neighbor, role, vrf` | VPC uptime in seconds |
| `nxos_vpc_consistency_status` | `name, neighbor, role, vrf, type, state, value` | 1 if consistent, else 0. `type` is one of `type1`, `type2`, `vlan`, or `Portchannel_<ifindex>` |
| `nxos_vpc_portchannel_health` | `name, neighbor, portchannel, consistency, state, thru_peerlink` | 1 if the VPC port-channel is healthy, else 0 |

## Endpoints

| Path | Description |
|---|---|
| `/metrics?target=<host>` | Scrapes `<host>` over SSH and returns its VPC metrics in Prometheus exposition format |
| `/health` | Returns JSON with the exporter's current SSH connection pool status |

## Configuration

The exporter is configured entirely through environment variables (see `.env`):

| Variable | Required | Default | Description |
|---|---|---|---|
| `SW_USERNAME` | Yes | — | SSH username used to log into switches |
| `SW_PASSWORD` | Yes | — | SSH password used to log into switches |
| `SSH_PORT` | No | `22` | SSH port to connect to on each switch |
| `COMMAND_TIMEOUT` | No | `10` | Per-command read timeout (seconds) on the switch |
| `LOG_LEVEL` | No | `INFO` | Python logging level (`DEBUG`, `INFO`, `WARNING`, ...) |

Copy `.env` to your `.env` and fill in real credentials before running.

**Note:** the exporter uses one shared SSH credential for every target switch.
All switches it scrapes must accept the same `SW_USERNAME` / `SW_PASSWORD`.

## Running with Docker

### Docker Compose

```yml
services:
  cisco-nxos-vpc-exporter:
    image: sinazare/cisco-nxos-vpc-exporter:1.0

    ports:
      - "9922:9922"

    env_file:
      - .env

    restart: unless-stopped

```

### Bash
```bash
cp .env .   # then edit with real credentials
docker compose up -d
```

This starts the exporter on port `9922`, restarting automatically unless
explicitly stopped (`restart: unless-stopped`).

## Prometheus configuration

Since this is a multi-target exporter (one process, many switches), scrape it
using the standard blackbox-exporter-style relabeling pattern — each switch
is a target passed via the `target` query parameter, and requests are
redirected to the exporter instance itself:

```yaml
scrape_configs:
  - job_name: cisco-nxos-vpc-exporter
    metrics_path: /metrics
    static_configs:
      - targets:
          - switch-a
          - switch-b
          - switch-c
          - 
        labels:
          team: network
          
    
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
        
      - target_label: __address__
        replacement: exporter-host:9922  # the exporter itself

# test using:        
# curl "http://localhost:9922/metrics?target=switch-a"

```

## Alerting rules

Alerting rules live in `nxos_vpc_alerts.yml` (Prometheus/Alertmanager rule
group `nxos_vpc_alerts`). Summary of what's covered:

**Exporter / scrape health**
- `NxosVpcExporterDown` — Prometheus can't reach the exporter's `/metrics` at all
- `NxosVpcDeviceScrapeFailed` — the exporter is up, but the SSH scrape of a specific switch failed
- `NxosVpcScrapeSlow` — scrape duration for a switch has stayed above 20s for 10m

**Peer link / keepalive**
- `NxosVpcPeerLinkDegraded` — VPC peer link unhealthy (dual-active risk if keepalive also fails)
- `NxosVpcPeerKeepaliveDown` — keepalive link down (treat as urgent if the peer link alert is also firing)
- `NxosVpcPeerLinkRecentlyFlapped` — VPC uptime under 10 minutes (recent (re)establishment)

**Consistency checks**
- `NxosVpcType1ConsistencyFailed` — global consistency failure (blocks VPC / suspends secondary VPCs)
- `NxosVpcType2ConsistencyFailed` — type-2 consistency failure (e.g. QoS/ACL mismatch)
- `NxosVpcVlanConsistencyFailed` — per-VLAN consistency failure
- `NxosVpcPortchannelConsistencyFailed` — consistency failure on a specific port-channel

**Port-channel health**
- `NxosVpcPortchannelDegraded` — a specific VPC port-channel is unhealthy

Critical alerts are considered to be routed with `channel: sms` in their labels; adjust
Alertmanager routing to match your notification setup.

## Project files

```
.
├── cisco_nxos_vpc_exporter.py   # exporter application
├── prometheus-alerts.yml        # Prometheus alerting rules
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
├── grafana-dashboard.json
└── README.md
```

## Requirements
(already satisfied in docker image)
- Python 3.11 (as pinned in the Dockerfile)
- `prometheus_client`
- `netmiko`
- `gunicorn`

## Notes / Operational tips

- The exporter must reach every target switch's management SSH over the
  network path from wherever it's deployed.
- `LOG_LEVEL=DEBUG` logs a full JSON dump of parsed VPC state per scrape,
  useful when troubleshooting label values but noisy for normal operation.
- Because SSH sessions persist across scrapes, killing/restarting the
  exporter container will force fresh SSH logins to every switch on the
  next scrape after restart.