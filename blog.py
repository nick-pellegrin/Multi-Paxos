

class User:
    def __init__(self, username):
        self.username = username


class Blog:
    def __init__(self):
        self.storage = {}

    # (key, value) = (username, [(op, title, content), (op, title, content), ...])
    def add_post(self, op, username, title, content):
        if username not in self.storage:
            self.storage[username] = []
        self.storage[username].append((op, title, content))
    
    def empty_storage(self):
        self.storage.clear()