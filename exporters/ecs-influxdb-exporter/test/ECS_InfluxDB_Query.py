def fetch_disk(target, registry):
    url = f"http://{target}"

    with InfluxDBClient(url=url, timeout=5000) as client:
        query_api = client.query_api()

        disk_used = Gauge(
            "ecs_disk_used_bytes",
            "ECS disk used space",
            ["node", "influx_addr", "path"],
            registry=registry,
        )

        disk_free = Gauge(
            "ecs_disk_free_bytes",
            "ECS disk free space",
            ["node", "influx_addr", "path"],
            registry=registry,
        )

        disk_total = Gauge(
            "ecs_disk_total_bytes",
            "ECS disk total space",
            ["node", "influx_addr", "path"],
            registry=registry,
        )

        query = f'''
        from(bucket: "{BUCKET}")
          |> range(start: -5m)
          |> filter(fn: (r) =>
              r["_measurement"] == "disk" and
              (r["_field"] == "used" or
               r["_field"] == "free" or
               r["_field"] == "total")
          )
          |> group(columns: ["host", "path", "_field"])
          |> last()
        '''

        results = {}

        for record in query_api.query_stream(query):
            host = record.values["host"]
            path = record.values.get("path", "unknown")
            field = record.get_field()
            value = record.get_value()

            key = (host, path)

            if key not in results:
                results[key] = {}

            results[key][field] = value

        for (host, path), m in results.items():
            used = m.get("used", 0)
            free = m.get("free", 0)
            total = m.get("total")

            if total is None:
                total = used + free

            disk_used.labels(node=host, influx_addr=target, path=path).set(used)
            disk_free.labels(node=host, influx_addr=target, path=path).set(free)
            disk_total.labels(node=host, influx_addr=target, path=path).set(total)






            ###############



def fetch_cpu(target, registry):
    url = f"http://{target}"

    with InfluxDBClient(url=url, timeout=5000) as client:
        query_api = client.query_api()

        cpu_usage = Gauge(
            "ecs_cpu_usage_percent",
            "ECS node CPU usage percentage",
            ["node", "influx_addr"],
            registry=registry,
        )

        query = f'''
        from(bucket: "{BUCKET}")
          |> range(start: -5m)
          |> filter(fn: (r) =>
              r["_measurement"] == "cpu" and
              r["_field"] == "usage_idle" and
              r["_field"] == "usage_system" and
              r["_field"] == "usage_user" and
              r["_field"] == "usage_iowait" and
              r["cpu"] == "cpu-total"
          )
          |> group(columns: ["host"])
          |> last()
        '''

        for record in query_api.query_stream(query):
            host = record.values["host"]
            idle = record.get_value()

            usage = 100 - idle
            cpu_usage.labels(node=host, influx_addr=target).set(usage)



            ###################################

def fetch_diskio(target, registry):
    url = f"http://{target}"

    with InfluxDBClient(url=url, timeout=5000) as client:
        query_api = client.query_api()

        # ---------------- Metrics ----------------
        diskio_read_bytes = Gauge(
            "ecs_diskio_read_bytes_total",
            "Disk read bytes",
            ["node", "influx_addr", "device"],
            registry=registry,
        )

        diskio_write_bytes = Gauge(
            "ecs_diskio_write_bytes_total",
            "Disk write bytes",
            ["node", "influx_addr", "device"],
            registry=registry,
        )

        diskio_reads = Gauge(
            "ecs_diskio_reads_total",
            "Disk read operations",
            ["node", "influx_addr", "device"],
            registry=registry,
        )

        diskio_writes = Gauge(
            "ecs_diskio_writes_total",
            "Disk write operations",
            ["node", "influx_addr", "device"],
            registry=registry,
        )

        diskio_read_latency = Gauge(
            "ecs_diskio_read_latency_ms",
            "Disk read latency (ms)",
            ["node", "influx_addr", "device"],
            registry=registry,
        )

        diskio_write_latency = Gauge(
            "ecs_diskio_write_latency_ms",
            "Disk write latency (ms)",
            ["node", "influx_addr", "device"],
            registry=registry,
        )

        # ---------------- Query ----------------
        query = f'''
        from(bucket: "{BUCKET}")
          |> range(start: -5m)
          |> filter(fn: (r) =>
              r["_measurement"] == "diskio"
          )
          |> group(columns: ["host", "name", "_field"])
          |> last()
        '''

        diskio_results = {}

        for record in query_api.query_stream(query):
            host = record.values["host"]
            device = record.values.get("name", "unknown")
            field = record.get_field()
            value = record.get_value()

            if host not in diskio_results:
                diskio_results[host] = {}

            if device not in diskio_results[host]:
                diskio_results[host][device] = {}

            diskio_results[host][device][field] = value

        # ---------------- Export ----------------
        for host, devices in diskio_results.items():
            for device, m in devices.items():
                read_bytes = m.get("read_bytes", 0)
                write_bytes = m.get("write_bytes", 0)
                reads = m.get("reads", 0)
                writes = m.get("writes", 0)
                read_time = m.get("read_time", 0)
                write_time = m.get("write_time", 0)

                # Avoid division by zero
                read_latency = (read_time / reads) if reads > 0 else 0
                write_latency = (write_time / writes) if writes > 0 else 0

                diskio_read_bytes.labels(
                    node=host, influx_addr=target, device=device
                ).set(read_bytes)

                diskio_write_bytes.labels(
                    node=host, influx_addr=target, device=device
                ).set(write_bytes)

                diskio_reads.labels(
                    node=host, influx_addr=target, device=device
                ).set(reads)

                diskio_writes.labels(
                    node=host, influx_addr=target, device=device
                ).set(writes)

                diskio_read_latency.labels(
                    node=host, influx_addr=target, device=device
                ).set(read_latency)

                diskio_write_latency.labels(
                    node=host, influx_addr=target, device=device
                ).set(write_latency)