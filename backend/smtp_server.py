"""
SMTP Server Implementation
Handles incoming email messages from other mail servers
"""

import asyncio
import socket
import ssl
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional
import threading
import re
import os

class SMTPServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 2525):
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.received_emails = []
        self.users = {}  # Simple user storage
        
    def start_server(self):
        """Start the SMTP server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.is_running = True
            
            print(f"SMTP Server started on {self.host}:{self.port}")
            
            # Start server in background thread
            server_thread = threading.Thread(target=self._run_server)
            server_thread.daemon = True
            server_thread.start()
            
        except Exception as e:
            print(f"Failed to start SMTP server: {e}")
            self.is_running = False
    
    def _run_server(self):
        """Run the SMTP server loop"""
        while self.is_running:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"New connection from {client_address}")
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.is_running:
                    print(f"Error accepting connection: {e}")
                break
    
    def _handle_client(self, client_socket: socket.socket, client_address: tuple):
        """Handle SMTP client connection"""
        try:
            # Send greeting
            self._send_response(client_socket, "220 CustomEmailServer SMTP Ready")
            
            # SMTP state machine
            state = "INIT"
            mail_from = None
            rcpt_to = []
            data_lines = []
            
            while True:
                try:
                    # Receive command
                    command = client_socket.recv(1024).decode('utf-8').strip()
                    if not command:
                        break
                    
                    print(f"RECV: {command}")
                    
                    # Parse command
                    cmd_parts = command.split(' ', 1)
                    cmd = cmd_parts[0].upper()
                    args = cmd_parts[1] if len(cmd_parts) > 1 else ""
                    
                    # Handle commands
                    if cmd == "EHLO" or cmd == "HELO":
                        self._send_response(client_socket, "250-CustomEmailServer")
                        self._send_response(client_socket, "250-SIZE 10240000")
                        self._send_response(client_socket, "250-8BITMIME")
                        self._send_response(client_socket, "250 HELP")
                        state = "READY"
                        
                    elif cmd == "MAIL":
                        if state == "READY":
                            # Parse FROM address
                            from_match = re.search(r'FROM:\s*<(.+?)>', args, re.IGNORECASE)
                            if from_match:
                                mail_from = from_match.group(1)
                                self._send_response(client_socket, "250 OK")
                                state = "MAIL"
                            else:
                                self._send_response(client_socket, "501 Invalid FROM address")
                        else:
                            self._send_response(client_socket, "503 Bad sequence of commands")
                    
                    elif cmd == "RCPT":
                        if state == "MAIL" or state == "RCPT":
                            # Parse TO address
                            to_match = re.search(r'TO:\s*<(.+?)>', args, re.IGNORECASE)
                            if to_match:
                                rcpt_to.append(to_match.group(1))
                                self._send_response(client_socket, "250 OK")
                                state = "RCPT"
                            else:
                                self._send_response(client_socket, "501 Invalid TO address")
                        else:
                            self._send_response(client_socket, "503 Bad sequence of commands")
                    
                    elif cmd == "DATA":
                        if state == "RCPT":
                            self._send_response(client_socket, "354 Start mail input; end with <CRLF>.<CRLF>")
                            state = "DATA"
                        else:
                            self._send_response(client_socket, "503 Bad sequence of commands")
                    
                    elif cmd == "QUIT":
                        self._send_response(client_socket, "221 Bye")
                        break
                    
                    elif cmd == "RSET":
                        mail_from = None
                        rcpt_to = []
                        data_lines = []
                        state = "READY"
                        self._send_response(client_socket, "250 OK")
                    
                    elif state == "DATA":
                        # Collect email data
                        if command == ".":
                            # End of data
                            email_data = "\r\n".join(data_lines)
                            self._process_received_email(mail_from, rcpt_to, email_data, client_address)
                            self._send_response(client_socket, "250 OK Message accepted")
                            
                            # Reset for next message
                            mail_from = None
                            rcpt_to = []
                            data_lines = []
                            state = "READY"
                        else:
                            # Remove dot-stuffing
                            if command.startswith(".."):
                                command = command[1:]
                            data_lines.append(command)
                    
                    else:
                        self._send_response(client_socket, "500 Command not recognized")
                
                except Exception as e:
                    print(f"Error processing command: {e}")
                    self._send_response(client_socket, "451 Temporary failure")
                    break
        
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        
        finally:
            client_socket.close()
    
    def _send_response(self, client_socket: socket.socket, response: str):
        """Send SMTP response to client"""
        try:
            client_socket.send(f"{response}\r\n".encode('utf-8'))
            print(f"SENT: {response}")
        except Exception as e:
            print(f"Error sending response: {e}")
    
    def _process_received_email(self, mail_from: str, rcpt_to: List[str], 
                               email_data: str, client_address: tuple):
        """Process received email message"""
        try:
            # Parse email headers and body
            headers, body = self._parse_email_message(email_data)
            
            # Create email record
            email_record = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'from': mail_from,
                'to': rcpt_to,
                'client_ip': client_address[0],
                'headers': headers,
                'body': body,
                'raw_message': email_data
            }
            
            # Store email
            self.received_emails.append(email_record)
            
            # Deliver to user mailboxes
            for recipient in rcpt_to:
                self._deliver_to_mailbox(recipient, email_record)
            
            print(f"Email received and processed: {mail_from} -> {rcpt_to}")
            
        except Exception as e:
            print(f"Error processing received email: {e}")
    
    def _parse_email_message(self, email_data: str) -> tuple:
        """Parse email message into headers and body"""
        try:
            # Split headers and body
            if '\r\n\r\n' in email_data:
                header_part, body_part = email_data.split('\r\n\r\n', 1)
            elif '\n\n' in email_data:
                header_part, body_part = email_data.split('\n\n', 1)
            else:
                header_part = email_data
                body_part = ""
            
            # Parse headers
            headers = {}
            for line in header_part.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
            
            return headers, body_part
            
        except Exception as e:
            print(f"Error parsing email message: {e}")
            return {}, email_data
    
    def _deliver_to_mailbox(self, recipient: str, email_record: Dict):
        """Deliver email to user's mailbox"""
        try:
            # Create user mailbox if it doesn't exist
            if recipient not in self.users:
                self.users[recipient] = {
                    'inbox': [],
                    'sent': [],
                    'drafts': []
                }
            
            # Add to inbox
            self.users[recipient]['inbox'].append(email_record)
            
            print(f"Email delivered to {recipient}'s inbox")
            
        except Exception as e:
            print(f"Error delivering email to {recipient}: {e}")
    
    def get_user_emails(self, email_address: str, folder: str = "inbox") -> List[Dict]:
        """Get emails from user's mailbox"""
        try:
            if email_address in self.users and folder in self.users[email_address]:
                return self.users[email_address][folder]
            return []
        except Exception as e:
            print(f"Error getting emails for {email_address}: {e}")
            return []
    
    def get_all_received_emails(self) -> List[Dict]:
        """Get all received emails"""
        return self.received_emails
    
    def stop_server(self):
        """Stop the SMTP server"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        print("SMTP Server stopped")
    
    def get_server_status(self) -> Dict:
        """Get server status"""
        return {
            'running': self.is_running,
            'host': self.host,
            'port': self.port,
            'total_emails': len(self.received_emails),
            'users': list(self.users.keys()),
            'user_count': len(self.users)
        }

# Global SMTP server instance
smtp_server = SMTPServer()