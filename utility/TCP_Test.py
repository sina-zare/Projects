import socket

def check_tcp_connection(hostname, port):
    # Create a TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)  # Set timeout for connection attempt

    try:
        # Try to connect to the given hostname and port
        sock.connect((hostname, port))
        print(f"\n\nConnection to {hostname}:{port} is successful.")
        return True
    except socket.error as e:
        print(f"\n\nConnection to {hostname}:{port} failed. Error: {e}")
        return False
    finally:
        # Close the socket
        sock.close()

while True:

    try:
        hostname = input(f"{'~' * 40}\nHostname: ").strip()
        port = int(input("Port: ").strip())

        check_tcp_connection(hostname, port)
        #print('\n')

    except Exception as err:
        print(f"\n\nError: {err}\n\n")
