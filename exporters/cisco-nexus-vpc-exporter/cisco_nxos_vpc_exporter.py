#!/usr/bin/env python3

"""
Cisco Nexus VPC Prometheus exporter.

Scrape pattern: GET /metrics?target=<switch-host>

Key design point: SSH sessions are pooled per target host and reused
across scrapes. We never open a new SSH connection just because a scrape
came in - we open one the first time we see a target, keep it alive, and
only reconnect if the session has actually died.

Note on multi-worker deployments: this pool is per PROCESS. If gunicorn
is started with multiple workers (-w N), each worker keeps its own
independent pool, so a given switch may end up with up to N live sessions
(one per worker that has handled it) rather than exactly one globally.
If you need a hard guarantee of a single session per device, run a single
worker with multiple threads instead:
    gunicorn -w 1 --threads 8 --timeout 30 -b 0.0.0.0:9922 cisco_nxos_vpc_exporter:app
This workload is I/O-bound (waiting on SSH), so threads scale it fine
without needing separate processes.
"""

from prometheus_client import (CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST)
from netmiko import ConnectHandler
from urllib.parse import parse_qs
import threading
import logging
import time
import json
import os
import re


logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("cisco_nxos_vpc_exporter")



# ---------------- Credentials / config ----------------
USERNAME = os.environ["SW_USERNAME"]
PASSWORD = os.environ["SW_PASSWORD"]
SSH_PORT = int(os.environ.get("SSH_PORT", 22))
COMMAND_TIMEOUT = int(os.environ.get("COMMAND_TIMEOUT", 10))

VPC_CMD = "sh vpc brief | json"
KEEPALIVE_CMD = "show vpc peer-keepalive | json"



# ---------------- Persistent connection pool (no classes) ----------------
# _connections: host -> live netmiko connection object (or missing/None)
# _host_locks: host -> threading.Lock, one per target so concurrent scrapes
#              of the SAME host serialize, while different hosts don't
#              block each other.
# _pool_lock: guards creation of entries in _host_locks itself.
_connections = {}
_host_locks = {}
_pool_lock = threading.Lock()


def _get_host_lock(host):
    with _pool_lock:
        lock = _host_locks.get(host)
        if lock is None:
            lock = threading.Lock()
            _host_locks[host] = lock
        return lock


def _build_device_params(host):
    return {
        "device_type": "cisco_nxos",
        "host": host,
        "username": USERNAME,
        "password": PASSWORD,
        "port": SSH_PORT,
        "timeout": 30,          # TCP connect timeout
        "auth_timeout": 20,     # SSH auth timeout
        "banner_timeout": 20,
        "keepalive": 30,        # TCP-level keepalive so idle sessions don't get dropped
    }


def _ensure_alive(host):
    """Return a live connection for host, reusing the cached one if
    possible, reconnecting only if it's actually dead. Caller must
    already hold _get_host_lock(host)."""
    conn = _connections.get(host)
    if conn is not None:
        try:
            if conn.is_alive():
                return conn
        except Exception:
            pass
        log.info("session to %s is dead, reconnecting", host)
        try:
            conn.disconnect()
        except Exception:
            pass
        _connections[host] = None

    log.info("opening new SSH session to %s", host)
    conn = ConnectHandler(**_build_device_params(host))
    _connections[host] = conn
    return conn


def run_commands(host, commands):
    """Run a list of commands over the persistent session for host.

    Reuses the existing session if alive. On any failure, drops the
    session and retries exactly once with a fresh connection before
    giving up (handles the case where the switch rebooted, the vty
    was cleared, etc. without paying the reconnect cost on every
    healthy scrape).
    """
    lock = _get_host_lock(host)
    with lock:
        last_err = None
        for attempt in range(2):
            try:
                conn = _ensure_alive(host)
                results = {
                    cmd: conn.send_command(cmd, read_timeout=COMMAND_TIMEOUT) for cmd in commands
                }
                return results
            except Exception as e:
                last_err = e
                log.warning("command run failed for %s (attempt %d): %s", host, attempt + 1, e)
                conn = _connections.get(host)
                if conn:
                    try:
                        conn.disconnect()
                    except Exception:
                        pass
                _connections[host] = None
        raise last_err


# ---------------- Metric collection ----------------
def _safe_lower(value):
    return value.lower() if isinstance(value, str) else ""


# ---------------- Persistent connection pool ----------------

def collect_vpc_metrics(switch_name, vpc_output, keepalive_output, registry):
    raw_data = json.loads(vpc_output)
    keepalive_data = json.loads(keepalive_output)

    #print(json_data = json.dumps(raw_data, indent=3))

    # Metric Definition
    nxos_vpc_peer_link_health = Gauge(
        "nxos_vpc_peer_link_health",
        "shows vpc peer link health status (0=degraded,1=healthy)",
        ["name", "neighbor", "reason", "domain_id", "role", "vrf", "state", "type1_consistency", "per_vlan_peer_consistency", "type2_consistency"],
        registry=registry,
    )

    nxos_vpc_peer_keepalive_health = Gauge(
        "nxos_vpc_peer_keepalive_health",
        "shows vpc peer keepalive health status (0=degraded,1=healthy)",
        ["name", "neighbor", "domain_id", "role", "vrf", "state"],
        registry=registry,
    )

    nxos_vpc_uptime = Gauge(
        "nxos_vpc_uptime",
        "shows vpc uptime (seconds)",
        ["name", "neighbor", "role", "vrf"],
        registry=registry,
    )

    nxos_vpc_consistency_status = Gauge(
        "nxos_vpc_consistency_status",
        "shows vpc consistency state for each type",
        ["name", "neighbor", "role", "vrf", "type", "state", "value"],
        registry=registry,
    )

    nxos_vpc_portchannel_health = Gauge(
        "nxos_vpc_portchannel_health",
        "shows vpc portchannel health status (0=degraded,1=healthy)",
        ["name", "neighbor", "portchannel", "consistency", "state", "thru_peerlink"],
        registry=registry,
    )

    # Extracting desired data
    vpc_keepalive_uptime = keepalive_data.get("vpc-peer-keepalive-up-time")
    vpc_uptime_seconds = None
    if vpc_keepalive_uptime:
        match = re.search(r"\((\d+)\)\s+seconds", vpc_keepalive_uptime)
        vpc_uptime_seconds = int(match.group(1)) if match else None

    vpc_vrf_name = keepalive_data.get("vpc-keepalive-vrf")
    vpc_neighbor = keepalive_data.get("vpc-keepalive-dest")
    vpc_peer_keepalive_status = raw_data.get("vpc-peer-keepalive-status")

    vpc_domain_id = raw_data.get("vpc-domain-id")
    vpc_role = raw_data.get("vpc-role")
    vpc_peer_status = raw_data.get("vpc-peer-status")
    vpc_peer_status_reason = raw_data.get("vpc-peer-status-reason")
    vpc_peer_consistency = raw_data.get("vpc-peer-consistency")
    vpc_type2_consistency_status = raw_data.get("vpc-type-2-consistency")
    vpc_type2_consistency_reason = raw_data.get("vpc-type-2-consistency-status")
    vpc_per_vlan_peer_consistency = raw_data.get("vpc-per-vlan-peer-consistency")
    vpc_peer_consistency_status = raw_data.get("vpc-peer-consistency-status")

    vpcs = {}
    for row in raw_data.get("TABLE_vpc").get("ROW_vpc"):
        vpcs[row["vpc-ifindex"]] = {
            "state": row.get("vpc-port-state", None),
            "consistency": row.get("vpc-consistency", None),
            "consistency_status": row.get("vpc-consistency-status", None),
            "thru_peerlink": row.get("vpc-thru-peerlink", None),
        }

    # vpcs = {}
    # for row in _rows_as_list(raw_data.get("TABLE_vpc", {}), "ROW_vpc"):
    #     vpcs[row.get("vpc-ifindex")] = {
    #         "state": row.get("vpc-port-state"),
    #         "consistency": row.get("vpc-consistency"),
    #         "consistency_status": row.get("vpc-consistency-status"),
    #         "thru_peerlink": row.get("vpc-thru-peerlink"),
    #     }


    # Metrics filling
    # link health
    nxos_vpc_peer_link_health.labels(
        name=switch_name,
        neighbor=vpc_neighbor,
        reason=vpc_peer_status_reason,
        domain_id=vpc_domain_id,
        role=vpc_role,
        vrf=vpc_vrf_name,
        state=vpc_peer_status,
        type1_consistency=vpc_peer_consistency,
        per_vlan_peer_consistency=vpc_per_vlan_peer_consistency,
        type2_consistency=vpc_type2_consistency_status
    ).set(1 if _safe_lower(vpc_peer_status) == "peer-ok" else 0)


    # keepalive health
    nxos_vpc_peer_keepalive_health.labels(
        name=switch_name,
        neighbor=vpc_neighbor,
        reason=vpc_peer_status_reason,
        domain_id=vpc_domain_id,
        role=vpc_role,
        vrf=vpc_vrf_name,
        state=vpc_peer_keepalive_status,
    ).set(1 if _safe_lower(vpc_peer_keepalive_status) == "peer-alive" else 0)


    # uptime
    nxos_vpc_uptime.labels(
        name=switch_name,
        neighbor=vpc_neighbor,
        role=vpc_role,
        vrf=vpc_vrf_name,
    ).set(vpc_uptime_seconds)


    # consistency
    # type 1
    nxos_vpc_consistency_status.labels(
        name=switch_name,
        neighbor=vpc_neighbor,
        role=vpc_role,
        vrf=vpc_vrf_name,
        type="type1",
        state=vpc_peer_consistency_status,
        value=vpc_peer_consistency,
    ).set(1 if _safe_lower(vpc_peer_consistency) == "consistent" else 0)

    #type 2
    nxos_vpc_consistency_status.labels(
        name=switch_name,
        neighbor=vpc_neighbor,
        role=vpc_role,
        vrf=vpc_vrf_name,
        type="type2",
        state=vpc_type2_consistency_reason,
        value=vpc_type2_consistency_status,
    ).set(1 if _safe_lower(vpc_type2_consistency_status) == "consistent" else 0)

    #type vlan
    nxos_vpc_consistency_status.labels(
        name=switch_name,
        neighbor=vpc_neighbor,
        role=vpc_role,
        vrf=vpc_vrf_name,
        type="vlan",
        state="null",
        value=vpc_per_vlan_peer_consistency,
    ).set(1 if _safe_lower(vpc_per_vlan_peer_consistency) == "consistent" else 0)


    #type portchannel consistency and portchannel health
    for vpc_index, vpc in vpcs.items():
        nxos_vpc_consistency_status.labels(
            name=switch_name,
            neighbor=vpc_neighbor,
            role=vpc_role,
            vrf=vpc_vrf_name,
            type=f"Portchannel_{vpc_index}",
            state=vpc.get("consistency_status"),
            value=vpc.get("consistency"),
        ).set(1 if _safe_lower(vpc.get("consistency")) == "consistent" else 0)

        state = vpc.get("state")
        nxos_vpc_portchannel_health.labels(
            name=switch_name,
            neighbor=vpc_neighbor,
            portchannel=vpc_index,
            consistency=vpc.get("consistency"),
            state=vpc.get("consistency_status"),
            thru_peerlink=vpc.get("thru_peerlink"),
        ).set(1 if str(state) == "1" else 0)


    log.debug(json.dumps({
        "switch_name": switch_name,
        "vpc_domain_id": vpc_domain_id,
        "vpc_neighbor": vpc_neighbor,
        "vpc_role": vpc_role,
        "vpc_peer_status": vpc_peer_status,
        "vpc_peer_status_reason": vpc_peer_status_reason,
        "vpc_peer_keepalive_status": vpc_peer_keepalive_status,
        "vpc_peer_consistency": vpc_peer_consistency,
        "vpc_per_vlan_peer_consistency": vpc_per_vlan_peer_consistency,
        "vpc_peer_consistency_status": vpc_peer_consistency_status,
        "vpc_type2_consistency_status": vpc_type2_consistency_status,
        "vpc_type2_consistency_reason": vpc_type2_consistency_reason,
        "vpcs": vpcs,
    }, indent=3))

def get_pool_health():
    alive = 0
    dead = 0
    hosts = {}

    with _pool_lock:
        connections = list(_connections.items())

    for host, conn in connections:
        try:
            if conn and conn.is_alive():
                alive += 1
                hosts[host] = "alive"
            else:
                dead += 1
                hosts[host] = "dead"
        except Exception:
            dead += 1
            hosts[host] = "dead"

    return {
        "status": "ok",
        "connections": len(connections),
        "alive": alive,
        "dead": dead,
        "hosts": hosts,
    }


# ---------------- WSGI App ----------------
def app(environ, start_response):
    path = environ.get("PATH_INFO", "")

    if path == "/health":
        health = get_pool_health()

        start_response(
            "200 OK",
            [("Content-Type", "application/json")]
        )

        return [json.dumps(health, indent=2).encode()]


    if path != "/metrics":
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"Not Found"]



    params = parse_qs(environ.get("QUERY_STRING", ""))
    target = params.get("target", [None])[0]

    if not target:
        start_response("400 Bad Request", [("Content-Type", "text/plain")])
        return [b"Missing target parameter"]



    registry = CollectorRegistry()

    # Exporter Metrics
    nxos_vpc_scrape_up = Gauge(
        "nxos_vpc_scrape_up",
        "1 if the scrape of this target succeeded",
        ["name"],
        registry=registry)

    nxos_vpc_scrape_duration_seconds = Gauge(
        "nxos_vpc_scrape_duration_seconds",
        "time spent collecting metrics for this target",
        ["name"],
        registry=registry)


    start = time.time()
    try:
        outputs = run_commands(target, [VPC_CMD, KEEPALIVE_CMD])
        collect_vpc_metrics(target, outputs[VPC_CMD], outputs[KEEPALIVE_CMD], registry)
        nxos_vpc_scrape_up.labels(name=target).set(1)
    except Exception as e:
        log.error("scrape of %s failed: %s", target, e)
        nxos_vpc_scrape_up.labels(name=target).set(0)
    finally:
        nxos_vpc_scrape_duration_seconds.labels(name=target).set(time.time() - start)

    output = generate_latest(registry)
    start_response("200 OK", [("Content-Type", CONTENT_TYPE_LATEST)])
    return [output]

# gunicorn -w 1 --threads 8 --timeout 30 -b 0.0.0.0:9922 cisco_nxos_vpc_exporter:app