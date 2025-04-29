#======================SERVER======================≠====
import socket  #import the socket module that is built-in with python
import time  #import time module
import threading	#import the threading module
import signal	#import signal for collecting shutdown signals
import sys	#import sys for program exit
import ssl	#import ssl for security

SERVER_HOST = "localhost"	
SERVER_PORT = 9090	   #Port to listen on
REREAD_ON_QUERY = True	#set as True as files change frequently


def start_server(config_file):
	'''The function starts the server and listens for incoming connections'''
	try:
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Initializing the socket for TCP
		server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Set socket to reuse address if already in use
		if hasattr(signal, 'SO_REUSEPORT'): # Usually used in Unix-like OS
			server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # Set socket to reuse port if already in use
		else: # Windows OS
			pass
		server_socket.bind((SERVER_HOST, SERVER_PORT))
		server_socket.listen(5)  # Listen up to 5 connections (backlog)
		print(f"Server is listening on {SERVER_HOST}:{SERVER_PORT}")
		
	 	#Set up signal handling for graceful shutdown
		signal.signal(signal.SIGINT, lambda s, f: server_signal(s, f, server_socket))
		signal.signal(signal.SIGTERM, lambda s, f: server_signal(s, f, server_socket))
		if hasattr(signal, 'SIGPIPE'): # Usually used in Unix-like OS
			signal.signal(signal.SIGPIPE, lambda s, f: server_signal(s, f, server_socket))
		else: # Windows OS
			pass
		
		while True:
			# Accept client connection
			client_socket, client_address = server_socket.accept()
			# Thread new client connection, using daemon
			client_thread = threading.Thread(target=client_handler, args=(client_socket, config_file, REREAD_ON_QUERY), daemon=True)
			client_thread.start()
			
	except Exception as e:
		print(f"Unexpected error: {e}")


def client_handler(client_socket, config_file, REREAD_ON_QUERY=False):
	'''Handles client connection and checks if the string exists in the file'''
	
	file_path = filePath(config_file, "linuxpath=")
	psk_key = filePath(config_file, "psk_key=")
	psk_switch = filePath(config_file, "psk_switch=")
	cert_path = filePath(config_file, "cert=")
	key_path = filePath(config_file, "key=")
	
	if not file_path or not psk_key or not psk_switch:
		# returns an error if values are not found
		print("File not found in configuration file.")
		return
	
	try:
		# If PSK authentication is enabled the condition will run
		if psk_switch == 'True':
		      context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
		      context.set_ciphers(psk_key)
		      context.load_cert_chain(cert_path, key_path)
		      client_socket = context.wrap_socket(client_socket, server_side=True)

		client_socket.settimeout(5)	#Set timeout to 5 seconds
		start_time = time.time()	# set start time
		file_content = None
		
		# Read the file once if REREAD_ON_QUERY is False
		if not REREAD_ON_QUERY:
			file_content = open(file_path, 'r').read()
			
		while True:
			# Receive data from client and strip \x00 character
			request = client_socket.recv(1024).rstrip(b'\x00').decode('utf-8')
			request_content = request.split("\n") #Split data with a new line
				
			if len(request_content) < 1: #Check for empty request
				print("Received an empty request.")
				break
			
			# Collecting specifics from request headers
			timestamp = time.ctime()
			http_method = request_content[0].split()[0]
			request_ip = client_socket.getsockname()[0]
			request_device = request_content[6].split()[1]
			execution_time = time.time() - start_time
			
			if http_method == "POST":
				# Re-read file on every query if REREAD_ON_QUERY is True
				if REREAD_ON_QUERY:
					file_content = open(file_path, 'r').read()
				#Extract query string from request and remove whitespace
				query_string = request_content[-1].split()
				# Check for string in file
				string_status = "STRING EXISTS\n" if query_string in file_content else "STRING NOT FOUND\n"
				response = (
					"HTTP/1.1 200 OK\n\n"
					f"{string_status}\n"
					f"DEBUG:\n{timestamp} | ExecutionTime:{execution_time:.2}s | Method:{http_method} | IP:{request_ip} | Device:{request_device} | Query:{query_string}\n"
					)
			elif http_method == "GET":
				response = (
					"HTTP/1.1 200 OK\n\n"
					f"DEBUG:\n{timestamp} | Method:{http_method} | IP:{request_ip} | Device:{request_device}\n"
					)	
			client_socket.sendall(response.encode('utf-8'))
	except IndexError:
		pass
	except (FileNotFoundError, ConnectionResetError, UnicodeDecodeError) as e:
		print(f"Error: {e}")
		client_socket.send(b"HTTP/1.1 400 Bad Request\n\n")
	except (BrokenPipeError, socket.timeout) as e:
		print(f"System error: {e}")
		client_socket.send(b"HTTP/1.1 500 Internal Server Error\n\n")
	except Exception as e:
		print(f"Unexpected error: {e}")
		client_socket.send(b"HTTP/1.1 500 Internal Server Error\n\n")
	finally:
		client_socket.close()


def server_signal(signal, frame, server_socket):
	'''Handles signal for graceful shutdown '''
	try:
		print('Shutting down server...')
		server_socket.close()
		sys.exit(0)
	except Exception as e:
		print(f"Unexpected error: {e}")


def filePath(config_file, start_with):
	"""Gets the file path from the configuration file."""
	try:
		with open(config_file, 'r') as file:
			for line in file:
				if line.startswith(start_with): 
					return line.split("=", 1)[1].strip()
	except FileNotFoundError:
		print("Configuration file not found.")
		return

if __name__ == "__main__":
	config_file = "config.txt"
	start_server(config_file)