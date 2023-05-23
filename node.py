import socket
import threading
import sys

from os import _exit
from sys import stdout
from time import sleep
from blockchain import Blockchain
from blockchain import Block
from blog import Blog

# keep waiting for user inputs
def get_user_input():
    while True:
        # wait for user input
        user_input = input()
        if user_input == "exit":
            in_sock.close()
            stdout.flush()
            _exit(0)
        elif user_input == "hello":
            for node in out_socks.values():
                node.sendall(f"hello from {idNum}".encode())




# Deal with Incoming Connections and Messages ------------------------------------------------------

# simulates network delay then handles received message
def handle_msg(data, conn, addr):
    sleep(3) 
    data = data.decode() # decode byte data into a string
    try:
        print(data)
    except:
        print(f"exception in handling request", flush=True)


# handle a new connection by waiting to receive from connection
def listen(conn, addr):
    while True:
        try:
            data = conn.recv(1024)
        except:
            print(f"exception in receiving from {addr[1]}", flush=True)
            break
        if not data:
            conn.close()
            print(f"connection closed from {addr[1]}", flush=True)
            break
        # spawn a new thread to handle message 
        threading.Thread(target=handle_msg, args=(data, conn, addr)).start()

# receive incoming connections and spawn a new thread to handle each connection
def get_connections():
    while True:
        try:
            conn, addr = in_sock.accept()
        except:
            print("exception in accept", flush=True)
            break
        print("connected to inbound client", flush=True)
        threading.Thread(target=listen, args=(conn, addr)).start()

# -------------------------------------------------------------------------------------------------



if __name__ == "__main__":

    # get node ID from command line argument
    id = str(sys.argv[1]) # ie "N1"
    idNum = int([*id][1]) # ie 1

    # Initializing
    blockchain = Blockchain()
    blog = Blog()
    out_socks = {}
    IP = socket.gethostname()
    PORT = 9000 + idNum
    QUEUE = []

    # create an inbound socket object to listen for incoming connections
    in_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    in_sock.bind((IP, PORT))
    in_sock.listen()
    threading.Thread(target=get_connections).start()

    # create outbound socket objects to connect to other nodes
    sleep(8)
    out_sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    out_sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    out_sock3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    out_sock4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if idNum == 1:
        out_sock1.connect((IP, 9002))
        out_sock2.connect((IP, 9003))
        out_sock3.connect((IP, 9004))
        out_sock4.connect((IP, 9005))
        out_socks[2] = out_sock1
        out_socks[3] = out_sock2
        out_socks[4] = out_sock3
        out_socks[5] = out_sock4
    if idNum == 2:
        out_sock1.connect((IP, 9001))
        out_sock2.connect((IP, 9003))
        out_sock3.connect((IP, 9004))
        out_sock4.connect((IP, 9005))
        out_socks[1] = out_sock1
        out_socks[3] = out_sock2
        out_socks[4] = out_sock3
        out_socks[5] = out_sock4
    if idNum == 3:
        out_sock1.connect((IP, 9001))
        out_sock2.connect((IP, 9002))
        out_sock3.connect((IP, 9004))
        out_sock4.connect((IP, 9005))
        out_socks[1] = out_sock1
        out_socks[2] = out_sock2
        out_socks[4] = out_sock3
        out_socks[5] = out_sock4
    if idNum == 4:
        out_sock1.connect((IP, 9001))
        out_sock2.connect((IP, 9002))
        out_sock3.connect((IP, 9003))
        out_sock4.connect((IP, 9005))
        out_socks[1] = out_sock1
        out_socks[2] = out_sock2
        out_socks[3] = out_sock3
        out_socks[5] = out_sock4
    if idNum == 5:
        out_sock1.connect((IP, 9001))
        out_sock2.connect((IP, 9002))
        out_sock3.connect((IP, 9003))
        out_sock4.connect((IP, 9004))
        out_socks[1] = out_sock1
        out_socks[2] = out_sock2
        out_socks[3] = out_sock3
        out_socks[4] = out_sock4

    
    # spawn a new thread to wait for user input
    threading.Thread(target=get_user_input).start() 



