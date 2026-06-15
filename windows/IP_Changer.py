import os

# Define network parameters
interface_name = "Wi-Fi"  # Replace with your Wi-Fi adapter name if different
static_ip = "172.26.76.148"
subnet_mask = "255.255.255.0"  # Equivalent to /24
gateway = "172.26.76.11"
dns = "10.202.10.102"

def set_static_ip():
    try:
        # Set static IP address and subnet mask
        os.system(f'netsh interface ip set address name="{interface_name}" static {static_ip} {subnet_mask} {gateway}')
        # Set DNS server
        os.system(f'netsh interface ip set dns name="{interface_name}" static {dns}')
        print("Static IP address configured successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    set_static_ip()
