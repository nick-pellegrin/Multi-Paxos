# Multi-Paxos Summary
This project simulates a distributed blog system with 5 server nodes that communicate using the Multi-Paxos message passing protocol.  The system is fault tolerant and replicated across all nodes.  The project creates a blog object to store the data on each node with a custom made blockchain to ensure data correctness.  In addition to the blog data object and blockchain, all data from both is backed up to text files so that data can be recovered in the event of a failure or to ensure correctness with other nodes.  

# Replicated Blog 
The blog object supports the following write operations:  
* **POST(username, title, content):** allows the user to make a new post to be added to the blog application.  
* **COMMENT(username, title, content):** allows the user to comment on an existing post with the specified (title), but if the post does not exist and error message is displayed to alert the user such a post does not exist.    

The blog object supports the following read operations:
* **VIEW:** allows the user to view the entire blog.
* **VIEW(username):** allows the user to view all posts and comments made by another user.
* **VIEW(title):** allows the user to view a post and all comments made on that post.

# Replicated Blockchain 
The replicated blockchain acts as a legder for all write operations made to the blog, and the blockchain ensures data correctness as an implicit functionality of blockchains. Each block on the blockchain consists of a single write operation for simplicity (however to scale this more operations should be stored per block).  

Each block in the blockchain consists of the following fields:  
* **Previous Hash Pointer (H):** This points to the previous block in the blockchain and is computed using SHA256, the hash pointer is calculated as SHA256(H_prev || T_prev || N_prev).
* **Write Operation (T):** this consists of the write operation to be stored in this block.
* **Nonce (N):** The nonce for this project was computed for a difficulty of 2 (meaning the nonce should be mined such that when hashed it results in 2 leading zeros).
* **Current Hash Pointer:** This hash pointer is calculated as SHA256(H || T || N) (this just makes it easier to fetch this pointer for the next block).

# Message Passing Protocol and Leader Election
The system operates asynchronously using Multi-Paxos consensus protocol leader election.  The following protocol is used anytime a new write operation is proposed by a user:
* **Leader Election:** If the node knows of know current leader, it proposes itself to be the new leader by sending out a (PREPARE) message to all other nodes.
* Upon receiving a (PREPARE) message, a node responds with (PROMISE) if it also doesn't know of another leader, however if it does know of another leader it pings the server designated as the leader to ensure it is still running.  If the current leader is still running it forwards the leader id to the node currently requesting to be the new leader, however if the leader ping times out then the node responds with (PROMISE).
* If the node requesting to be leader recieves a leader id from any of the other nodes, it cancels its own leader election and forwards the post request to the current leader.  Otherwise, if the node recieves <PROMISE> from a majority of other nodes and recieves no leader id, it designates itself as the leader.
* **Replication Phase:** Once there is a leader agreed upon by the majority of nodes, the replication phase can start.  If the node making the post request is not the leader, it forwards the request to the leader.  If the leader is the one making the post request or receives a forwarded post request, it then sends out an (ACCEPT) message along with the post to all other nodes.
* Upon receiving an (ACCEPT) message from the leader, a node replies with (ACCEPTED) so that the leader can ensure a majority of the network aggrees on the proposed post request.
* Once the leader recieves an (ACCEPTED) from a majority of nodes in the system, it can enter the decision phase.
* **Decission Phase:** Once in the decision phase, the leader mines the new block to be added to the blockchain and adds it to the blockchain, adds the post to the blog data object, and backs up the operation to the blog and blockchain text files specific to that server node.  After doing this it sends out a (DECIDE) message to all other nodes in the network.
* Upon receiving a (DECIDE) message from the leader, a node also mines the new block to be added to the blockchain and adds it to the blockchain, adds the post to the blog data object, and backs up the operation to the blog and blockchain text files specific to that server node.  Then that node responds back to the leader with a (DECIDED) message to communicate that the post operation has been replicated on that node.

# Fault Tolerance and Recovery
This distributed system protocol allows for less than a majority of nodes to fail and still function properly.  Additionally, should a network partition occur a new leader election will be triggered on the side partitioned without the leader.  After a network partition results in two or more conflicting blogs/blockchains, if the partitioned networks reconnect they merge their respective data without repetition and select a single leader from the partitioned networks previous leaders based on lowest id number.  If at any point a node forwards a post request to the leader and doesn't hear back from the leader with an (ACCEPT) message after a certain timeout a leader election will be triggered.  If a node is down for an extended period of time while post operations continue to be added to the blog/blockchain, upon restarting and reconnecting to the network it compares its logs with all other nodes and consolidates all the data added after it went offline to catch up with the other nodes.
