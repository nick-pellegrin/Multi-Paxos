import hashlib


class Block:
    def __init__(self, previous_hash, op, username, title, content):
        self.previous_hash = previous_hash
        self.op = op
        self.username = username
        self.title = title
        self.content = content
        self.nonce = 0
        self.hash = self.calculate_hash()


    def calculate_hash(self):
        hash_string = str(self.previous_hash) + str(self.op) + str(self.username) + str(self.title) + str(self.content) + str(self.nonce)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        # bin_hash = "{0:08b}".format(int(encoded[:2], 16))
        # while self.hash[:difficulty] != "0" * difficulty:
        while int(self.hash[0], 16) >= 2:
            self.nonce += 1
            self.hash = self.calculate_hash()


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.chain[0].hash = self.chain[0].previous_hash
        self.difficulty = 3

    def create_genesis_block(self):
        return Block("0" * 64, "genesis_sender", "genesis_receiver", 0, 0)

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, new_block):
        # new_block.previous_hash = self.get_latest_block().hash
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)

    def empty_chain(self):
        self.chain.clear()
        self.chain = [self.create_genesis_block()]
        self.chain[0].hash = self.chain[0].previous_hash
    
    def get_chain(self):
        posts = []
        for block in self.chain[1:]:
            # posts.append((block.op, block.username, block.title, block.content, block.previous_hash))
            posts.append((block.op, block.username, block.title, block.content, block.hash))
        return posts
    
    def get_userposts(self, username):
        posts = []
        for block in self.chain:
            if block.username == username:
                posts.append((block.title, block.content))
        return posts
    
    def get_postcoments(self, title):
        posts = []
        for block in self.chain:
            if block.title == title and block.op == "post":
                posts.append((block.title, block.username, block.content))
        for block in self.chain:
            if block.title == title and block.op == "coment":
                posts.append((block.username, block.content))
        return posts
    
    def get_depth(self):
        return len(self.chain)
    
    def get_postexists(self, title):
        for block in self.chain:
            if block.title == title and block.op == "post":
                return True
        return False
    
