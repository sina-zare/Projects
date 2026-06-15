import socket

def resolve_fqdn(fqdn):
    try:
        # Attempt to resolve the FQDN to an IP address
        ip_address = socket.gethostbyname(fqdn)
        print(f"Successfully resolved {fqdn} to {ip_address}")
        return ip_address
    except socket.gaierror as e:
        # Handle the error if the FQDN cannot be resolved
        print(f"Failed to resolve {fqdn}: {e}")
        return None

# Example usage
fqdn = "www.youtasdasdube.com"
resolved_ip = resolve_fqdn(fqdn)
if resolved_ip:
    print(f"Resolution successful: {resolved_ip}")
else:
    print("Resolution failed.")

