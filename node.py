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
import math
import os, fnmatch

"""
TODO:
                            - implement timeout + re-election process (if needed)
                            - implement prepare rejection if leader already exists and isn't down
                                - possible edge case if leader fails and initiates election proceess upon restart
                                - all nodes should change leader_id back to None after leader timeout
                            - implement fail link and fix link (to simulate partitioning)
                            - implement copying longest log when loading backup (extra credit)

                            PRIORITY FOR DEMO (according to project description):
                            - (1) (done) Normal multi paxos operation with replicated log
                            - (2) (done) Crash failure and recovery from disk/reconection to network
                            - (3) (todo) Fail link and fix link (to simulate partitioning) (nothing completed yet)
                            - (4) (done) Blog post application (finish comment functionality)

MORE TODO:
    - IMPLEMENT NEW ELECTION WHEN LEADER FAILS LINK
    - IMPLEMENT CONCURRENT POST COMMANDS. HIGHER NUMID WINS

How to use Blog:
    Post Format: post_<username>_<title>_<content>
    Comment Format: comment_<username>_<title>_<content>
    Blog Format: blog
    View Format: view <username>
    Read Format: read_<title>
"""


def get_user_input():
    """keep waiting for user inputs"""
    global leader_id, ballotNum, highestPromiseID
    blockchain_filename = f"N{idNum}_blockchain_log.txt"
    blog_filename = f"N{idNum}_blog_log.txt"
    while True:
        user_input = input()
        if user_input == "exit":
            in_sock.close()
            stdout.flush()
            _exit(0)
        if user_input == "reconnect":
            for node in out_socks.values():
                node.sendall(f"RECONNECT {idNum}".encode())
        if user_input == "load":
            bc_log_length = 0
            blog_log_length = 0
            try:
                lines = open(blockchain_filename, 'r').readlines()
                bc_log_length = len(lines)
                lines = open(blog_filename, 'r').readlines()
                blog_log_length = len(lines)
            except:
                print("NO LOGS FOUND", flush=True)
            print("CHECKING NEIGHBOR LOGS", flush=True)
            for root, dirs, files in os.walk('.'):
                for file in fnmatch.filter(files, '*_blockchain_log.txt'):
                    other_lines = open(file, 'r').readlines()
                    if len(other_lines) > bc_log_length:
                        out = open(blockchain_filename, 'w')
                        out.writelines(other_lines)
                        out.close()
            for root, dirs, files in os.walk('.'):
                for file in fnmatch.filter(files, '*_blog_log.txt'):
                    other_lines = open(file, 'r').readlines()
                    if len(other_lines) > blog_log_length:
                        out = open(blog_filename, 'w')
                        out.writelines(other_lines)
                        out.close()
            try:
                blockchain.empty_chain()
                blog.empty_storage()
                new_lines = open(blockchain_filename, 'r').readlines()
                for line in new_lines:
                    # line.strip()
                    line = line[:-1] # remove newline character
                    new_block = Block(blockchain.get_latest_block().hash, line.split("_")[1], line.split("_")[2], line.split("_")[3], line.split("_")[4])
                    blockchain.add_block(new_block)
                new_lines = open(blog_filename, 'r').readlines()
                for line in new_lines:
                    # line.strip()
                    line = line[:-1] # remove newline character
                    blog.add_post(line.split("_")[0], line.split("_")[1], line.split("_")[2], line.split("_")[3])
                print("LOAD COMPLETE", flush=True)
            except:
                print("LOAD FAILED", flush=True)

            print("Fetching current leader", flush=True)
            out_socks[1].sendall(f"WHOLEAD {idNum}".encode())
            print("Sent leader request, now updating leader", flush=True)

        if user_input.split("_")[0] == "post" or user_input.split("_")[0] == "comment": 
            if user_input.split("_")[0] == "comment" and blockchain.get_postexists(user_input.split("_")[2]) == False:
                print("POST DOES NOT EXIST", flush=True)
            if user_input.split("_")[0] == "post" and blockchain.get_postexists(user_input.split("_")[2]) == True:
                print("DUPLICATE TITLE", flush=True)
            elif leader_id == idNum: # act as leader
                ballotNum += 1
                QUEUE.append(user_input)
                new_block = Block(blockchain.get_latest_block().hash, user_input.split("_")[0], user_input.split("_")[1], user_input.split("_")[2], user_input.split("_")[3])
                new_block.mine_block(blockchain.difficulty)
                for node in out_socks.values():
                    node.sendall(f"ACCEPT_{idNum}_{blockchain.get_depth()}_{new_block.op}_{new_block.username}_{new_block.title}_{new_block.content}_{new_block.nonce}_{ballotNum}".encode())
                threading.Thread(target=initiate_timeout).start()
            elif leader_id == None: # act as proposer
                ballotNum += 1
                highestPromiseID = idNum
                for node in out_socks.values():
                    node.sendall(f"PREPARE_{idNum}_{blockchain.get_depth()}_{user_input}_{ballotNum}".encode())
                    sleep(0.2)
                threading.Thread(target=initiate_timeout).start()
            else: # act as acceptor
                try:
                    out_socks[int(leader_id)].sendall(f"FORWARD_{idNum}_{user_input}".encode())
                except:
                    print("No connection to leader. Attempting to become new leader", flush=True)
                    # START NEW ELECTION

        if user_input.split(" ")[0] == "crash":
            in_sock.close()
            stdout.flush()
            _exit(0)
        if user_input.split(" ")[0] == "failLink":
            out_socks[int(user_input.split(" ")[1])].sendall(f"FAIL {idNum}".encode())
            del out_socks[int(user_input.split(" ")[1])]
            print(f"Connection to N{user_input.split(' ')[1]} failed", flush=True)
        if user_input.split(" ")[0] == "fixLink":
            add_outbound_connection(int(user_input.split(" ")[1]))
            out_socks[int(user_input.split(" ")[1])].sendall(f"FIX {idNum}".encode())
            print(f"Connection to N{user_input.split(' ')[1]} fixed", flush=True)
        if user_input.split(" ")[0] == "blockchain":
            chain = blockchain.get_chain()
            if len(chain) == 0:
                print("[]", flush=True)
            else:
                for block in chain:
                    print(block, flush=True)
        if user_input.split(" ")[0] == "queue":
            print(QUEUE, flush=True)
        if user_input.split(" ")[0] == "blog":
            if blockchain.get_depth() == 1:
                print("BLOG EMPTY", flush=True)
            else:
                titles = []
                counter = 0
                for block in blockchain.chain:
                    if counter == 0:
                        counter += 1            
                        continue
                    if block.op == "post":
                        titles.append(block.title)
                for title in titles:
                    print(str(title), flush=True)         
        if user_input.split(" ")[0] == "view":
            this_user = user_input.split(" ")[1]
            content = []
            for block in blockchain.chain:
                if block.username == this_user:
                    content.append((block.title, block.content))
            if len(content) == 0:
                print("NO POSTS", flush=True)
            else:
                for post in content:
                    print(str(post[0]) + ": " + str(post[1]), flush=True)
        if user_input.split("_")[0] == "read":
            this_title = user_input.split("_")[1]
            content = []
            for block in blockchain.chain:
                if block.title == this_title:
                    content.append((block.username, block.content))
            if len(content) == 0:
                print("POST NOT FOUND", flush=True)
            else:
                for post in content:
                    print(str(post[0]) + ": " + str(post[1]), flush=True)
        
        # FOR TESTING PURPOSES ONLY
        if user_input == "leader":
            print(str(leader_id) + "   " + str(type(leader_id)))
        if user_input == "nodes":
            print(out_socks.keys())
                




# Deal with Incoming Connections and Messages ------------------------------------------------------

def handle_msg(data, conn, addr):
    """simulates network delay then handles received message"""
    global QUEUE, promises, accepted, leader_id, timeout_continue, ballotNum, highestPromiseID
    blockchain_filename = f"N{idNum}_blockchain_log.txt"
    blog_filename = f"N{idNum}_blog_log.txt"
    sleep(3) 
    data = data.decode()
    try:
        if data.split("_")[0] == "PREPARE" and int(data.split("_")[2]) >= blockchain.get_depth():
            print(f"recieved PREPARE from N{data.split('_')[1]}")
            if (ballotNum < int(data.split("_")[7])):
                ballotNum = int(data.split("_")[7])
            if (int(data.split('_')[1]) >= highestPromiseID):
                highestPromiseID = int(data.split('_')[1])
            op_string = data.split("_")[3] + "_" + data.split("_")[4] + "_" + data.split("_")[5] + "_" + data.split("_")[6]
            out_socks[int(data.split("_")[1])].sendall(f"PROMISE_{idNum}_{op_string}_{ballotNum}".encode())
        if data.split("_")[0] == "PROMISE":
            print(f"recieved PROMISE from N{data.split('_')[1]}")
            promises += 1
            if promises >= math.ceil((len(out_socks) + 1)/2):
                timeout_continue = False
                promises = 0
                leader_id = idNum
                op_string = data.split("_")[2] + "_" + data.split("_")[3] + "_" + data.split("_")[4] + "_" + data.split("_")[5]
                QUEUE.append(op_string)
                new_block = Block(blockchain.get_latest_block().hash, data.split("_")[2], data.split("_")[3], data.split("_")[4], data.split("_")[5])
                new_block.mine_block(blockchain.difficulty)
                for node in out_socks.values():
                    node.sendall(f"ACCEPT_{idNum}_{blockchain.get_depth()}_{new_block.op}_{new_block.username}_{new_block.title}_{new_block.content}_{new_block.nonce}_{ballotNum}".encode())
                    sleep(0.2)
                threading.Thread(target=initiate_timeout).start()
        if data.split("_")[0] == "ACCEPT" and int(data.split("_")[2]) >= blockchain.get_depth():
            print(f"recieved ACCEPT from N{data.split('_')[1]}")
            if (int(data.split("_")[8]) > ballotNum or (int(data.split("_")[8]) == ballotNum and int(data.split("_")[1]) == highestPromiseID)):
                leader_id = int(data.split("_")[1])
                op_string = data.split("_")[3] + "_" + data.split("_")[4] + "_" + data.split("_")[5] + "_" + data.split("_")[6]
                out_socks[int(data.split("_")[1])].sendall(f"ACCEPTED_{idNum}_{op_string}".encode())
                with open(blockchain_filename, "a") as log:
                        log.write(f"TENATIVE {op_string}\n")
            else:
                print(f"not replying to ACCEPT from N{data.split('_')[1]}")
        if data.split("_")[0] == "ACCEPTED":
            sleep(0.5) 
            print(f"recieved ACCEPTED from N{data.split('_')[1]}")
            if len(QUEUE) > 0:
                accepted += 1
            if (accepted >= math.ceil((len(out_socks) + 1)/2)) and len(QUEUE) > 0:
                timeout_continue = False
                accepted = 0
                new_block = Block(blockchain.get_latest_block().hash, data.split("_")[2], data.split("_")[3], data.split("_")[4], data.split("_")[5])
                blockchain.add_block(new_block)
                with open(blockchain_filename, "a") as log:
                    log.write(f"CONFIRMED_{new_block.op}_{new_block.username}_{new_block.title}_{new_block.content}\n")
                blog.add_post(data.split("_")[2], data.split("_")[3], data.split("_")[4], data.split("_")[5])
                with open(blog_filename, "a") as log:
                    log.write(f"{new_block.op}_{new_block.username}_{new_block.title}_{new_block.content}\n")
                QUEUE.pop(0)
                if data.split("_")[2] == "post":
                    print(f"NEW POST: {data.split('_')[4]} from {data.split('_')[3]}")
                if data.split("_")[2] == "comment":
                    print(f"NEW COMMENT: on {data.split('_')[4]} from {data.split('_')[3]}")
                promises, accepted, highestPromiseID = 0, 0, 0
                for node in out_socks.values():
                    node.sendall(f"DECIDE_{idNum}_{new_block.op}_{new_block.username}_{new_block.title}_{new_block.content}_{ballotNum}".encode())
        if data.split("_")[0] == "DECIDE":
            print(f"recieved DECIDE from N{data.split('_')[1]}")
            if (int(data.split("_")[6]) >= ballotNum):
                ballotNum = int(data.split("_")[6])
            highestPromiseID = 0
            new_block = Block(blockchain.get_latest_block().hash, data.split("_")[2], data.split("_")[3], data.split("_")[4], data.split("_")[5])
            blockchain.add_block(new_block)
            lines = open(blockchain_filename, 'r').readlines()
            lines[-1] = f"CONFIRMED_{new_block.op}_{new_block.username}_{new_block.title}_{new_block.content}\n"
            out = open(blockchain_filename, 'w')
            out.writelines(lines)
            out.close()
            blog.add_post(data.split("_")[2], data.split("_")[3], data.split("_")[4], data.split("_")[5])
            with open(blog_filename, "a") as log:
                    log.write(f"{new_block.op}_{new_block.username}_{new_block.title}_{new_block.content}\n")
            if data.split("_")[2] == "post":
                print(f"NEW POST: {data.split('_')[4]} from {data.split('_')[3]}")
            if data.split("_")[2] == "comment":
                print(f"NEW COMMENT: on {data.split('_')[4]} from {data.split('_')[3]}")
        if data.split("_")[0] == "FORWARD":
            print(f"recieved FORWARD from {data.split('_')[1]}")
            ballotNum += 1
            if leader_id == idNum:
                op_string = data.split("_")[2] + "_" + data.split("_")[3] + "_" + data.split("_")[4] + "_" + data.split("_")[5]
                QUEUE.append(op_string)
                new_block = Block(blockchain.get_latest_block().hash, data.split("_")[2], data.split("_")[3], data.split("_")[4], data.split("_")[5])
                new_block.mine_block(blockchain.difficulty)
                for node in out_socks.values():
                    node.sendall(f"ACCEPT_{idNum}_{blockchain.get_depth()}_{new_block.op}_{new_block.username}_{new_block.title}_{new_block.content}_{new_block.nonce}_{ballotNum}".encode())
                    sleep(0.2)
            else:
                out_socks[leader_id].sendall(f"FORWARD_{idNum}_{op_string}".encode())
        if data.split(" ")[0] == "RECONNECT":
            print(f"reconnecting to N{data.split(' ')[1]}")
            add_outbound_connection(int(data.split(" ")[1]))
        if data.split(" ")[0] == "FAIL":
            del out_socks[int(data.split(" ")[1])]
            print(f"Connection to N{data.split(' ')[1]} failed", flush=True)
            if int(data.split(" ")[1]) == leader_id:
                print("Warning: Connection to leader failed!")
        if data.split(" ")[0] == "FIX":
            add_outbound_connection(int(data.split(" ")[1]))
            print(f"Connection to N{data.split(' ')[1]} fixed", flush=True)
        if data.split(" ")[0] == "WHOLEAD":
            print("Leader identity requested", flush=True)
            
        if data.split(" ")[0] == "LEADER":
            print("Leader identity received", flush=True)
            leader_id = int(data.split(" ")[1])
            print(f"Leader is N{leader_id}", flush=True)

    except Exception:
        traceback.print_exc()


def listen(conn, addr):
    """handle a new connection by waiting to receive from connection"""
    while True:
        try:
            data = conn.recv(1024)
        except:
            conn.close()
            delete_outbound_connections()
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
    counter = 0
    while True:
        try:
            conn, addr = in_sock.accept()
        except:
            print("exception in accept", flush=True)
            break
        print("connected to inbound client", flush=True)
        counter += 1 
        if counter == 4: # Chris: Update This to 4 for Final Testing
            print("all clients connected", flush=True)
        threading.Thread(target=listen, args=(conn, addr)).start()


def delete_outbound_connections():
    """after failed inbound conn, search for corresponding outbound conn and delete it"""
    failed_connections = []
    for id, node in out_socks.items():
        try:
            node.sendall("PING".encode())
        except:
            failed_connections.append(id)
    for id in failed_connections:
        del out_socks[id]


def add_outbound_connection(id):
    """add a new outbound connection to node with id"""
    if id not in out_socks:
        try:
            out_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            out_sock.connect((IP, 9000 + id))
            out_socks[id] = out_sock
        except:
            print(f"failed to connect to outbound client N{id}", flush=True)


def initiate_timeout():
    global timeout_continue
    timeout_count = 0
    for i in range(10):
        sleep(1)
        timeout_count += 1
        if timeout_continue == False:
            timeout_continue = True
            break
    if timeout_count == 10:
        print("TIMEOUT")
    



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
    ballotNum = 0
    highestPromiseID = 0
    IP = socket.gethostname()
    PORT = 9000 + idNum
    QUEUE = []
    timeout_continue = True

    # create an inbound socket object to listen for incoming connections
    in_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    in_sock.bind((IP, PORT))
    in_sock.listen()
    threading.Thread(target=get_connections).start()

    # create outbound socket objects to connect to other nodes
    sleep(8)

    if idNum == 1:
        add_outbound_connection(2)
        add_outbound_connection(3)
        add_outbound_connection(4)
        add_outbound_connection(5)
 
    if idNum == 2:
        add_outbound_connection(1)
        add_outbound_connection(3)
        add_outbound_connection(4)
        add_outbound_connection(5)


    if idNum == 3:
        add_outbound_connection(1)
        add_outbound_connection(2)
        add_outbound_connection(4)
        add_outbound_connection(5)


    if idNum == 4:
        add_outbound_connection(1)
        add_outbound_connection(2)
        add_outbound_connection(3)
        add_outbound_connection(5)

    if idNum == 5:
        add_outbound_connection(1)
        add_outbound_connection(2)
        add_outbound_connection(3)
        add_outbound_connection(4)

    
    # spawn a new thread to wait for user input
    threading.Thread(target=get_user_input).start() 



