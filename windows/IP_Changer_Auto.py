import os

# Define network parameters
interface_name = "Wi-Fi"  # Replace with your Wi-Fi adapter name if different

def set_dhcp():
    try:
        # Set IP configuration to DHCP
        os.system(f'netsh interface ip set address name="{interface_name}" source=dhcp')
        # Set DNS configuration to automatic
        os.system(f'netsh interface ip set dns name="{interface_name}" source=dhcp')
        print("IP and DNS configuration set to DHCP successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    set_dhcp()
