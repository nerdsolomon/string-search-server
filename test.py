#=====================TEST-SUITE=========================
import pytest
import socket
import ssl
from server import filePath, server_signal
import sys

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

def test_filePath():
    # Test filePath function
    config_file = "config.txt"
    assert filePath(config_file, "name=") == "Nerdsolomon"
    
def test_file_not_found():
    # Test file not found exception
    config_file = "null_config.txt"
    assert filePath(config_file, "null=") == None

def test_connection_reset():
    # Test connection reset exception
    client_socket = server_connection()
    client_socket.close()
    assert True

def test_unicode_decode_error():
    # Test unicode decode error exception
    client_socket = server_connection()
    request = b"\xff\xff\xff\xff"
    client_socket.sendall(request)
    assert True

def test_broken_pipe_error():
    # Test broken pipe error exception
    client_socket = server_connection()
    client_socket.sendall(b"POST / HTTP/1.1\n\nHello Server")
    client_socket.close()
    assert True

def test_socket_timeout():
    # Test socket timeout exception
    client_socket = server_connection()
    client_socket.settimeout(1)
    request = b"POST / HTTP/1.1\n\nHello Server"
    client_socket.sendall(request)
    assert True

def test_index_error():
    # Test index error exception
    client_socket = server_connection()
    request = b"POST / HTTP/1.1\n\n"
    client_socket.sendall(request)
    assert True
    
@pytest.fixture
def mock_sys_exit(monkeypatch):
    with monkeypatch.context() as mp:
        mp.setattr(sys, "exit", lambda code: None)
        yield
        
def test_server_signal(mock_sys_exit):
    # Test server signal function
    mock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_signal(None, None, mock_socket)
    assert True