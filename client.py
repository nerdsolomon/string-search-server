#=======================CLIENT===========================
import socket
import ssl
import time
from server import filePath

SERVER_HOST = "localhost"	
SERVER_PORT = 9090

def server_connection():
    ''' Connects the script to the server '''
    try:
    	config_file = "config.txt"
    	psk_key = filePath(config_file, "psk_key=")
    	psk_switch = filePath(config_file, "psk_switch=")
    	host_name = filePath(config_file, "name=")
    	cert_path = filePath(config_file, "cert=")
    
    	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    	client_socket.connect((SERVER_HOST, SERVER_PORT))
    	# If PSK authentication is enabled the condition will run
    	if psk_switch == 'True':
        	context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        	context.set_ciphers(psk_key)
        	context.check_hostname = True
        	context.load_verify_locations(cert_path)
        	client_socket = context.wrap_socket(client_socket, server_hostname=host_name)
    	return client_socket
    except Exception as e:
    	print(f"Unexpected error: {e}")

def send_request(file_size):
	''' Send a post request to server with a query file '''
	try:
	   client_socket = server_connection()
	   query = open(f'{file_size}.txt', 'r').read()
	   request = f"POST / HTTP/1.1\n\n" + query
	   client_socket.sendall(request.encode("utf-8"))
	   client_socket.recv(1024)
	   client_socket.close()
	except ConnectionResetError as e:	# Reached system limit
		print(f"Error: {e}")
    
def file_size_execution_time():
    ''' Prints execution time for each file size '''
    try:
    	file_sizes = [10000, 50000, 100000, 500000, 1000000]
    	for file_size in file_sizes:
    		start_time = time.time()
    		send_request(file_size)
    		execution_time = time.time() - start_time
    		print(f"ExecutionTime:{execution_time:.2f}s FileSize:{file_size}")
    except Exception as e:
    	print(f"Unexpected error: {e}")
    	
def num_queries_per_file_size():
    ''' Prints execution time of number of queries for each file size '''
    try:
    	num_queries = [1, 10, 50, 100, 500]
    	file_sizes = [10000, 50000, 100000, 500000, 1000000]
    	for num_query in num_queries:
        	for file_size in file_sizes:
        	   start_time = time.time()
        	   for _ in range(num_query):
        	   	send_request(file_size)
        	   execution_time = time.time() - start_time
        	   print(f"ExecutionTime:{execution_time:.2f}s Queries:{num_query} FileSize:{file_size}")
    except Exception as e:
        print(f"Unexpected error: {e}")
            
file_size_execution_time()
num_queries_per_file_size()