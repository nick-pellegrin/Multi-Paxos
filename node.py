import socket
import threading
import sys

from os import _exit
from sys import stdout
from time import sleep
from blockchain import Blockchain
from blockchain import Block
from blog import Blog
import traceback


def get_user_input():
    """keep waiting for user inputs"""
    global leader_id
    while True:
        user_input = input()
        if user_input == "exit":
            in_sock.close()
            stdout.flush()
            _exit(0)
        if user_input.split(" ")[0] == "post" or user_input.split(" ")[0] == "comment":
            if leader_id == idNum: # act as leader
                QUEUE.append(user_input)
                new_block = Block(blockchain.get_latest_block().hash, user_input.split(" ")[0], user_input.split(" ")[1], user_input.split(" ")[2], user_input.split(" ")[3])
                new_block.mine_block(blockchain.difficulty)
                for node in out_socks.values():
                    node.sendall(f"ACCEPT {idNum} {blockchain.get_depth()} {new_block.op} {new_block.username} {new_block.title} {new_block.content} {new_block.nonce}".encode())
            elif leader_id == None: # act as proposer
                for node in out_socks.values():
                    node.sendall(f"PREPARE {idNum} {blockchain.get_depth()} {user_input}".encode())
            else: # act as acceptor
                out_socks[leader_id].sendall(f"FORWARD {idNum} {user_input}".encode())
        if user_input.split(" ")[0] == "crash":
            pass
        if user_input.split(" ")[0] == "failLink":
            pass
        if user_input.split(" ")[0] == "fixLink":
            pass
        if user_input.split(" ")[0] == "blockchain":
            print(blockchain.get_chain(), flush=True)
        if user_input.split(" ")[0] == "queue":
            print(QUEUE, flush=True)
        if user_input.split(" ")[0] == "blog":
            if blockchain.get_depth() == 1:
                print("BLOG EMPTY", flush=True)
            else:
                titles = []
                for block in blockchain.chain:
                    titles.append(block.title)
                print(titles, flush=True)
        if user_input.split(" ")[0] == "view":
            this_user = user_input.split(" ")[1]
            content = []
            for block in blockchain.chain:
                if block.username == this_user:
                    content.append((block.title, block.content))
            if len(content) == 0:
                print("NO POSTS", flush=True)
            else:
                print(content, flush=True)
        if user_input.split(" ")[0] == "read":
            this_title = user_input.split(" ")[1]
            content = []
            for block in blockchain.chain:
                if block.title == this_title:
                    content.append((block.username, block.content))
            if len(content) == 0:
                print("POST NOT FOUND", flush=True)
            else:
                print(content, flush=True)
        
        # FOR TESTING PURPOSES ONLY
        if user_input == "leader":
            print(leader_id)
                




# Deal with Incoming Connections and Messages ------------------------------------------------------

def handle_msg(data, conn, addr):
    """simulates network delay then handles received message"""
    global promises, accepted, leader_id
    sleep(3) 
    data = data.decode()
    try:
        if data.split(" ")[0] == "PREPARE" and int(data.split(" ")[2]) >= blockchain.get_depth():
            print(f"recieved PREPARE from {data.split(' ')[1]}")
            op_string = data.split(" ")[3] + " " + data.split(" ")[4] + " " + data.split(" ")[5] + " " + data.split(" ")[6]
            out_socks[int(data.split(" ")[1])].sendall(f"PROMISE {idNum} {op_string}".encode())
        if data.split(" ")[0] == "PROMISE":
            print(f"recieved PROMISE from {data.split(' ')[1]}")
            promises += 1
            if promises >= 2:
                promises = 0
                leader_id = idNum
                op_string = data.split(" ")[2] + " " + data.split(" ")[3] + " " + data.split(" ")[4] + " " + data.split(" ")[5]
                QUEUE.append(op_string)
                new_block = Block(blockchain.get_latest_block().hash, data.split(" ")[2], data.split(" ")[3], data.split(" ")[4], data.split(" ")[5])
                new_block.mine_block(blockchain.difficulty)
                for node in out_socks.values():
                    node.sendall(f"ACCEPT {idNum} {blockchain.get_depth()} {new_block.op} {new_block.username} {new_block.title} {new_block.content} {new_block.nonce}".encode())
        if data.split(" ")[0] == "ACCEPT" and int(data.split(" ")[2]) >= blockchain.get_depth():
            print(f"recieved ACCEPT from {data.split(' ')[1]}")
            leader_id = data.split(" ")[1]
            op_string = data.split(" ")[3] + " " + data.split(" ")[4] + " " + data.split(" ")[5] + " " + data.split(" ")[6]
            out_socks[int(data.split(" ")[1])].sendall(f"ACCEPTED {idNum} {op_string}".encode())
        if data.split(" ")[0] == "ACCEPTED":
            print(f"recieved ACCEPTED from {data.split(' ')[1]}")
            accepted += 1
            if accepted >= 2:
                accepted = 0
                new_block = Block(blockchain.get_latest_block().hash, data.split(" ")[2], data.split(" ")[3], data.split(" ")[4], data.split(" ")[5])
                blockchain.add_block(new_block)
                blog.add_post(data.split(" ")[2], data.split(" ")[3], data.split(" ")[4], data.split(" ")[5])
                QUEUE.pop(0)
                for node in out_socks.values():
                    node.sendall(f"DECIDE {idNum} {new_block.op} {new_block.username} {new_block.title} {new_block.content}".encode())
        if data.split(" ")[0] == "DECIDE":
            print(f"recieved DECIDE from {data.split(' ')[1]}")
            new_block = Block(blockchain.get_latest_block().hash, data.split(" ")[2], data.split(" ")[3], data.split(" ")[4], data.split(" ")[5])
            blockchain.add_block(new_block)
            blog.add_post(data.split(" ")[2], data.split(" ")[3], data.split(" ")[4], data.split(" ")[5])
        if data.split(" ")[0] == "FORWARD":
            print(f"recieved FORWARD from {data.split(' ')[1]}")
            if leader_id == idNum:
                op_string = data.split(" ")[2] + " " + data.split(" ")[3] + " " + data.split(" ")[4] + " " + data.split(" ")[5]
                QUEUE.append(op_string)
                new_block = Block(blockchain.get_latest_block().hash, data.split(" ")[2], data.split(" ")[3], data.split(" ")[4], data.split(" ")[5])
                new_block.mine_block(blockchain.difficulty)
                for node in out_socks.values():
                    node.sendall(f"ACCEPT {idNum} {blockchain.get_depth()} {new_block.op} {new_block.username} {new_block.title} {new_block.content} {new_block.nonce}".encode())
            else:
                out_socks[leader_id].sendall(f"FORWARD {idNum} {op_string}".encode())
    # except:
    #     print(f"exception in handling request", flush=True)
    except Exception:
        traceback.print_exc()


def listen(conn, addr):
    """handle a new connection by waiting to receive from connection"""
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


def get_connections():
    """receive incoming connections and spawn a new thread to handle each connection"""
    while True:
        try:
            conn, addr = in_sock.accept()
        except:
            print("exception in accept", flush=True)
            break
        print("connected to inbound client", flush=True)
        threading.Thread(target=listen, args=(conn, addr)).start()

# --------------------------------------------------------------------------------------------------




if __name__ == "__main__":

    # get node ID from command line argument
    id = str(sys.argv[1]) # ie "N1"
    idNum = int([*id][1]) # ie 1

    # Initializing
    blockchain = Blockchain()
    blog = Blog()
    out_socks = {}
    leader_id = None
    promises = 0
    accepted = 0
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
        out_socks[2] = out_sock1
        out_socks[3] = out_sock2
 
    if idNum == 2:
        out_sock1.connect((IP, 9001))
        out_sock2.connect((IP, 9003))
        out_socks[1] = out_sock1
        out_socks[3] = out_sock2

    if idNum == 3:
        out_sock1.connect((IP, 9001))
        out_sock2.connect((IP, 9002))
        out_socks[1] = out_sock1
        out_socks[2] = out_sock2


    # if idNum == 1:
    #     out_sock1.connect((IP, 9002))
    #     out_sock2.connect((IP, 9003))
    #     out_sock3.connect((IP, 9004))
    #     out_sock4.connect((IP, 9005))
    #     out_socks[2] = out_sock1
    #     out_socks[3] = out_sock2
    #     out_socks[4] = out_sock3
    #     out_socks[5] = out_sock4
    # if idNum == 2:
    #     out_sock1.connect((IP, 9001))
    #     out_sock2.connect((IP, 9003))
    #     out_sock3.connect((IP, 9004))
    #     out_sock4.connect((IP, 9005))
    #     out_socks[1] = out_sock1
    #     out_socks[3] = out_sock2
    #     out_socks[4] = out_sock3
    #     out_socks[5] = out_sock4
    # if idNum == 3:
    #     out_sock1.connect((IP, 9001))
    #     out_sock2.connect((IP, 9002))
    #     out_sock3.connect((IP, 9004))
    #     out_sock4.connect((IP, 9005))
    #     out_socks[1] = out_sock1
    #     out_socks[2] = out_sock2
    #     out_socks[4] = out_sock3
    #     out_socks[5] = out_sock4
    # if idNum == 4:
    #     out_sock1.connect((IP, 9001))
    #     out_sock2.connect((IP, 9002))
    #     out_sock3.connect((IP, 9003))
    #     out_sock4.connect((IP, 9005))
    #     out_socks[1] = out_sock1
    #     out_socks[2] = out_sock2
    #     out_socks[3] = out_sock3
    #     out_socks[5] = out_sock4
    # if idNum == 5:
    #     out_sock1.connect((IP, 9001))
    #     out_sock2.connect((IP, 9002))
    #     out_sock3.connect((IP, 9003))
    #     out_sock4.connect((IP, 9004))
    #     out_socks[1] = out_sock1
    #     out_socks[2] = out_sock2
    #     out_socks[3] = out_sock3
    #     out_socks[4] = out_sock4

    
    # spawn a new thread to wait for user input
    threading.Thread(target=get_user_input).start() 



