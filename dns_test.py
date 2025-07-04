import dns.resolver
import socket
import ssl
import sys

def test_dns_resolver():
    """Test DNS resolver functionality"""
    print("\n=== Testing DNS MX Record Lookup ===")
    
    domains = ["gmail.com", "yahoo.com"]
    
    for domain in domains:
        try:
            print(f"\nLooking up MX records for {domain}:")
            mx_records = dns.resolver.resolve(domain, 'MX')
            
            for record in mx_records:
                print(f"  Priority: {record.preference}, Server: {record.exchange}")
            
            # Try to connect to the first MX server
            first_mx = str(mx_records[0].exchange).rstrip('.')
            print(f"\nTesting connection to {first_mx}:25")
            
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((first_mx, 25))
                
                # Read greeting
                response = sock.recv(1024).decode('utf-8')
                print(f"Server greeting: {response.strip()}")
                
                # Send EHLO
                sock.sendall(f"EHLO example.com\r\n".encode('utf-8'))
                response = sock.recv(1024).decode('utf-8')
                print(f"EHLO response: {response.strip()}")
                
                # Check if STARTTLS is supported
                if "STARTTLS" in response:
                    print("STARTTLS is supported")
                    
                    # Send STARTTLS command
                    sock.sendall("STARTTLS\r\n".encode('utf-8'))
                    response = sock.recv(1024).decode('utf-8')
                    print(f"STARTTLS response: {response.strip()}")
                    
                    if response.startswith("220"):
                        # Wrap socket with TLS
                        context = ssl.create_default_context()
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        
                        ssl_sock = context.wrap_socket(sock, server_hostname=first_mx)
                        print("TLS connection established")
                        
                        # Send EHLO again over TLS
                        ssl_sock.sendall(f"EHLO example.com\r\n".encode('utf-8'))
                        response = ssl_sock.recv(1024).decode('utf-8')
                        print(f"EHLO (TLS) response: {response.strip()}")
                        
                        # Send QUIT
                        ssl_sock.sendall("QUIT\r\n".encode('utf-8'))
                        ssl_sock.close()
                    else:
                        print("STARTTLS failed")
                else:
                    print("STARTTLS is not supported")
                    
                    # Send QUIT
                    sock.sendall("QUIT\r\n".encode('utf-8'))
                
                sock.close()
                
            except Exception as e:
                print(f"Connection error: {e}")
            
        except Exception as e:
            print(f"Error looking up MX records for {domain}: {e}")

if __name__ == "__main__":
    test_dns_resolver()