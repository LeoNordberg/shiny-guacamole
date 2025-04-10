import socket
import pickle
import select
import serverClientShares as scs

# Creates a network class
class Network:
    def __init__(self, ip):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = 5555
        self.addr = (self.ip, self.port)

    # Connects the network object to a specified server
    def connect(self):
        try:
            self.client.connect(self.addr)
            worked = True
        except socket.error as e:
            print("Connection failed")
            print(e)
            worked = False
        return worked

    # Sends a message to the server
    def sendMessage(self, msg):
        message = msg.encode(scs.FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(scs.FORMAT)
        send_length += b' ' * (scs.HEADER - len(send_length))
        try:
            self.client.send(send_length)
            self.client.send(message)
        except:
            return '!NOT_SENT'

    # Sends an object to the server
    # NOT IN USE
    def sendItem(self, item):
        item = pickle.dumps(item)
        item_size = scs.deep_getsizeof(item)
        send_length = str(item_size).encode(scs.FORMAT)
        send_length += b' ' * (scs.HEADER - len(send_length))
        self.client.send(send_length)
        self.client.send(item)

    # Tries to retrieve a message from the server
    def retrieveMessage(self):
        data, _, _ = select.select([self.client], [], [], 0)

        if data:
            msg_length = self.client.recv(scs.HEADER).decode(scs.FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = self.client.recv(msg_length).decode(scs.FORMAT)
                return msg
            
    # Tries to retrieve an object from the server
    # NOT IN USE
    def retrieveItem(self):
        data, _, _ = select.select([self.client], [], [], 0)

        if data:
            item_size = self.client.recv(scs.HEADER).decode(scs.FORMAT)
            if item_size:
                item_size = int(item_size)
                item = pickle.loads(self.client.recv(item_size))
                return item