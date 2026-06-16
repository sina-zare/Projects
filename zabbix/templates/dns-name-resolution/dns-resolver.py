#!/usr/bin/env python3

import sys
import json
import time
import dns.resolver

hostname = sys.argv[1]
dns_server = sys.argv[2]

result = {
    "success": False,
    "ip": "",
    "response_time_ms": 0,
    "error": ""
}

try:
    resolver = dns.resolver.Resolver()
    resolver.nameservers = dns_server.split(",")

    start = time.perf_counter()

    answer = resolver.resolve(hostname, "A")

    end = time.perf_counter()

    result["success"] = True
    result["ip"] = answer[0].to_text()
    result["response_time_ms"] = round((end - start) * 1000, 2)

except Exception as e:
    result["error"] = str(e)

print(json.dumps(result))
