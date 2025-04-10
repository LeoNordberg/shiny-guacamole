import socket
import threading
import time
import select
import copy
import pickle
import random

import serverClientShares as scs


# Holds info a bout the server
infoAboutServer = {'serverShutdown' : False,    # True if the server should shutdown
                   'clientId'  :0,              # The current id a new client will recieve if joined
                   'numberOfPlayers' : 0,       # The current number of players connected to the server
                   'clients' : {}               # The clients id and their order joining {id : order} eg {2 : 0, 5 : 1, 8 : 2}
                                                # Mostly if a player leaves the order and their ids are kept
                   }

# General info about the card games
generalGameInfo = {'currentGame' : False,       # The current games name will be stored here
                   'currentTurn' : 0,           # Whose players turn it is
                   'deckOfCards' : [],          # The current deck of cards and all of its cards
                   'playedCards' : [],          # The cards that have been played
                   'infoAboutPlayers' : [],     # Info about the players, will be filled with the info about the game eg turnTenInfo for turn ten
                   'card' : [],                 # A place to store a certain card incase it is needed
                   'stage' : '',                # The current stage of the game
                   'position' : []              # The positions that the players finish in
                   }

# The bool turns True when the action is to be performed
# Makes sure the clients are synced during certain actions
syncClients = {'dealCards' : [False, []],
               'clearDeck' : [False, []],
               'start' : [False, []],
               'changeStage' : [False, [], False],          # The second bool is for making sure the server doesnt try to change stage multiple times while the clients are updating their stage
               'switch' : [False, []],
               'emptyDeck' : [False, []],
               'handNum' : [False, []]
               }

# Holds the connected clients id and position
clients = {}


# A function that sends a string to the connected client
def sendMessage(conn, msg):
    message = msg.encode(scs.FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(scs.FORMAT)
    send_length += b' ' * (scs.HEADER - len(send_length))
    try:
        conn.send(send_length)
        conn.send(message)
    except:
        return '!NOT_SENT'

# A function that sends an object to the connected client
# NOT IN USE
def sendItem(conn, item):
    item = pickle.dumps(item)
    item_size = scs.deep_getsizeof(item)
    send_length = str(item_size).encode(scs.FORMAT)
    send_length += b' ' * (scs.HEADER - len(send_length))
    conn.client.send(send_length)
    conn.client.send(item)

# A function that retrieves a string from the connected client
def retrieveMessage(conn):
    data, _, _ = select.select([conn], [], [], 0)

    if data:
        msg_length = conn.recv(scs.HEADER).decode(scs.FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(scs.FORMAT)
            return msg

# A function that retrieves an object from the connected client
# NOT IN USE
def retrieveItem(conn):
    data, _, _ = select.select([conn], [], [], 0)

    if data:
        item_size = conn.recv(scs.HEADER).decode(scs.FORMAT)
        if item_size:
            item_size = int(item_size)
            item = pickle.loads(conn.recv(item_size))
            return item

# handles the clients connection to the server
def handle_client(conn, addr, id):
    print(f"[CONNECTION] {addr} connected.")

    global syncClients
    global generalGameInfo
    global infoAboutServer

    playedCardsOffSync = []
    playerTurnOffSync = 0
    connected = True
    
    # Sends the current turn and the players positon in the game
    sendMessage(conn, scs.TURN + ',' + str(generalGameInfo['currentTurn']) + ',' + str(clients[id]))
    while connected:
        if infoAboutServer['serverShutdown']:
            connected = False

        msg = retrieveMessage(conn)
        # If there is a message to process
        if msg:
            # Disconnects the client
            if msg == scs.DISCONNECT_MESSAGE:
                connected = False

            # Shuts down the server
            elif msg == scs.SERVER_SHUTDOWN_MESSAGE:
                infoAboutServer['serverShutdown'] = True
                connected = False

            # Changes the game to turn ten
            elif msg == (scs.GAME + ',' + scs.TURNTEN):
                generalGameInfo.update({'currentGame' : scs.TURNTEN})

                generalGameInfo['stage'] = scs.TURNTEN_PRE

                syncClients['clearDeck'][0] = True
                syncClients['dealCards'][0] = True
                syncClients['start'][0] = True

            # Goes to the next turn
            elif msg == scs.TURN:
                generalGameInfo['currentTurn'] += 1
            
            # Performs actions for the game turn ten
            elif generalGameInfo['currentGame'] == scs.TURNTEN:
                # Acts on the deal command from the client
                if msg == scs.DEAL_CARDS_MESSAGE:
                    syncClients['dealCards'][0] = True

                # Updates the clients current stage in the game
                elif scs.decodeStringMessage(msg)[0] == scs.TURNTEN_STAGE:
                    if scs.decodeStringMessage(msg)[1] == scs.TURNTEN_WAIT:
                        syncClients['changeStage'][0] = True
                        syncClients['changeStage'][2] = True
                        generalGameInfo['infoAboutPlayers'][clients[id]]['wait'] = True

                    if scs.decodeStringMessage(msg)[1] == scs.TURNTEN_END:
                        generalGameInfo['infoAboutPlayers'][clients[id]]['stage'] = scs.TURNTEN_END
                        generalGameInfo['infoAboutPlayers'][clients[id]]['wait'] = True

                # Acts on the clearDeck command from the client
                elif msg == scs.TURNTEN_CLEARDECK:
                    syncClients['clearDeck'][0] = True
                
                # Sends a card for the client to add to their hand if the deck is not empty
                elif msg == scs.TURNTEN_PICKUPCARD:
                    if len(generalGameInfo['deckOfCards']) != 0:
                        chosenCard = random.randint(0, len(generalGameInfo['deckOfCards']) - 1)
                        generalGameInfo['infoAboutPlayers'][clients[id]]['hand'].append(generalGameInfo['deckOfCards'][chosenCard])
                        sendMessage(conn, scs.TURNTEN_READ + ',' + scs.encodeStringMessage(generalGameInfo['deckOfCards'][chosenCard]))
                        generalGameInfo['deckOfCards'].pop(chosenCard)

                # Lets the client play a card from their hand
                elif scs.decodeStringMessage(msg)[0] == scs.TURNTEN_PLAY:
                    card = scs.decodeStringMessage(msg)
                    card.pop(0)
                    card[0] = int(card[0])
                    generalGameInfo['playedCards'].append(card)
                    generalGameInfo['infoAboutPlayers'][clients[id]]['hand'].remove(card)
                    syncClients['handNum'] = [True, []]

                # Lets the client play a card from their minideck1
                elif scs.decodeStringMessage(msg)[0] == scs.TURNTEN_MINIDECK1:
                    card = scs.decodeStringMessage(msg)
                    card.pop(0)
                    card[0] = int(card[0])
                    generalGameInfo['playedCards'].append(card)
                    generalGameInfo['infoAboutPlayers'][clients[id]]['minideck1'].remove(card)
                    syncClients['switch'][0] = True

                # Lets the client play a card from their minideck2
                elif scs.decodeStringMessage(msg)[0] == scs.TURNTEN_MINIDECK2:
                    card = scs.decodeStringMessage(msg)
                    card.pop(0)
                    card[0] = int(card[0])
                    generalGameInfo['playedCards'].append(card)
                    generalGameInfo['infoAboutPlayers'][clients[id]]['minideck2'].remove(card)
                    syncClients['switch'][0] = True

                # Lets the client play a card from their minideck3
                elif scs.decodeStringMessage(msg)[0] == scs.TURNTEN_MINIDECK3:
                    card = scs.decodeStringMessage(msg)
                    card.pop(0)
                    card[0] = int(card[0])
                    generalGameInfo['playedCards'].append(card)
                    generalGameInfo['infoAboutPlayers'][clients[id]]['minideck3'].remove(card)
                    syncClients['switch'][0] = True

                # Gives the player a chance in the game turn ten (if they cant play they pickup a card and try to play it)
                elif msg == scs.TURNTEN_CHANCE:
                    randomCard = random.randint(0, len(generalGameInfo['deckOfCards']) - 1)
                    sendMessage(conn, scs.TURNTEN_READ + ',' + scs.encodeStringMessage(generalGameInfo['deckOfCards'][randomCard]))
                    generalGameInfo['infoAboutPlayers'][clients[id]]['hand'].append(generalGameInfo['deckOfCards'][randomCard])
                    generalGameInfo['deckOfCards'].pop(randomCard)

                # Pickups the pile for the client
                elif msg == scs.TURNTEN_PICKUPPILE:
                    for card in generalGameInfo['playedCards']:
                        generalGameInfo['infoAboutPlayers'][clients[id]]['hand'].append(card)
                    syncClients['clearDeck'][0] = True

                # Switches the two cards the player wanted to switch in the pregame
                elif scs.decodeStringMessage(msg)[0] == scs.TURNTEN_SWITCH:
                    message = scs.decodeStringMessage(msg)
                    cards = []
                    selectedCards = [[int(message[1]), message[2]], [int(message[3]), message[4]]]

                    # Checks the position of the two cards that need to be switched and stores them as cards = [[x1, y1], [x2, y2]]
                    for i in range(2):
                        if selectedCards[i] in generalGameInfo['infoAboutPlayers'][clients[id]]['hand']:
                            cards.append([generalGameInfo['infoAboutPlayers'][clients[id]]['hand'].index(selectedCards[i]), 1])
                        elif selectedCards[i] == generalGameInfo['infoAboutPlayers'][clients[id]]['minideck1'][len(generalGameInfo['infoAboutPlayers'][clients[id]]['minideck1']) - 1]:
                            cards.append([0, 0])
                        elif selectedCards[i] == generalGameInfo['infoAboutPlayers'][clients[id]]['minideck2'][len(generalGameInfo['infoAboutPlayers'][clients[id]]['minideck2']) - 1]:
                            cards.append([1, 0])
                        elif selectedCards[i] == generalGameInfo['infoAboutPlayers'][clients[id]]['minideck3'][len(generalGameInfo['infoAboutPlayers'][clients[id]]['minideck3']) - 1]:
                            cards.append([2, 0])

                    
                    # Switches the first card
                    if cards[0][1] == 1:
                        generalGameInfo['infoAboutPlayers'][clients[id]]['hand'][cards[0][0]] = selectedCards[1]
                    else:
                        if cards[0][0] == 0:
                            generalGameInfo['infoAboutPlayers'][clients[id]]['minideck1'][1] = selectedCards[1]
                        elif cards[0][0] == 1:
                            generalGameInfo['infoAboutPlayers'][clients[id]]['minideck2'][1] = selectedCards[1]
                        elif cards[0][0] == 2:
                            generalGameInfo['infoAboutPlayers'][clients[id]]['minideck3'][1] = selectedCards[1]

                    # Switches the second card
                    if cards[1][1] == 1:
                        generalGameInfo['infoAboutPlayers'][clients[id]]['hand'][cards[1][0]] = selectedCards[0]
                    else:
                        if cards[1][0] == 0:
                            generalGameInfo['infoAboutPlayers'][clients[id]]['minideck1'][len(generalGameInfo['infoAboutPlayers'][clients[id]]['minideck1']) - 1] = selectedCards[0]
                        elif cards[1][0] == 1:
                            generalGameInfo['infoAboutPlayers'][clients[id]]['minideck2'][len(generalGameInfo['infoAboutPlayers'][clients[id]]['minideck2']) - 1] = selectedCards[0]
                        elif cards[1][0] == 2:
                            generalGameInfo['infoAboutPlayers'][clients[id]]['minideck3'][len(generalGameInfo['infoAboutPlayers'][clients[id]]['minideck3']) - 1] = selectedCards[0]

                    cards = []
                    selectedCards = []
                    syncClients['switch'][0] = True

            # Performs actions for the game go fish
            elif generalGameInfo['currentGame'] == scs.GOFISH:
                pass

            # End of message reaction from client
        

        # Does the server side logic for the game turn ten
        if generalGameInfo['currentGame'] == scs.TURNTEN:
            # Sends the finishing position of the client to them
            try:
                if generalGameInfo['infoAboutPlayers'][clients[id]]['stage'] == scs.TURNTEN_END and generalGameInfo['infoAboutPlayers'][clients[id]]['wait']:
                    generalGameInfo['position'].append(id)
                    sendMessage(conn, scs.POSITION + ',' + str(generalGameInfo['position'].index(id) + 1))
                    generalGameInfo['infoAboutPlayers'][clients[id]]['wait'] = False
            except:
                pass

            # Clears the clients deck
            if id not in syncClients['clearDeck'][1] and syncClients['clearDeck'][0]:
                sendMessage(conn, scs.TURNTEN_CLEARDECK)
                syncClients['clearDeck'][1].append(id)

            # Tells the client that the deck is empty
            if id not in syncClients['emptyDeck'][1] and syncClients['emptyDeck'][0]:
                sendMessage[conn, scs.TURNTEN_EMPTYDECK]
                syncClients['emptyDeck'][1].append(id)

            # Send information about the other clients minidecks and hand to the client
            if id not in syncClients['switch'][1] and syncClients['switch'][0]:
                for i in range(len(clients)):
                    for j in range(2):
                        text = scs.TURNTEN_SWITCH + ',' + str(i)
                        text += ',minideck1,' + str(j)
                        try:
                            text += ',' + scs.encodeStringMessage(generalGameInfo['infoAboutPlayers'][i]['minideck1'][j])
                        except:
                            text += ',' + scs.TURNTEN_NOCARD
                        sendMessage(conn, text)

                    for j in range(2):
                        text = scs.TURNTEN_SWITCH + ',' + str(i)
                        text += ',minideck2,' + str(j)
                        try:
                            text += ',' + scs.encodeStringMessage(generalGameInfo['infoAboutPlayers'][i]['minideck2'][j])
                        except:
                            text += ',' + scs.TURNTEN_NOCARD
                        sendMessage(conn, text)

                    for j in range(2):
                        text = scs.TURNTEN_SWITCH + ',' + str(i)
                        text += ',minideck3,' + str(j)
                        try:
                            text += ',' + scs.encodeStringMessage(generalGameInfo['infoAboutPlayers'][i]['minideck3'][j])
                        except:
                            text += ',' + scs.TURNTEN_NOCARD
                        sendMessage(conn, text)
                    text = scs.TURNTEN_SWITCH + ',' + str(i) + ',hand,' + scs.TURNTEN_PLACEHOLDER + ',' + scs.TURNTEN_PLACEHOLDER + ',' + str(len(generalGameInfo['infoAboutPlayers'][i]['hand']))
                    sendMessage(conn, text)
                    text = ''

                syncClients['switch'][1].append(id)

            # Sends the other clients number of cards to the client
            if id not in syncClients['handNum'][1] and syncClients['handNum'][0]:
                text = scs.TURNTEN_SWITCH + ',' + str(i) + ',hand,' + scs.TURNTEN_PLACEHOLDER + ',' + scs.TURNTEN_PLACEHOLDER + ',' + str(len(generalGameInfo['infoAboutPlayers'][i]['hand']))
                sendMessage(conn, text)
                syncClients['handNum'].append(id)

            # Updates the cards that have been played
            if playedCardsOffSync != generalGameInfo['playedCards']:
                for card in generalGameInfo['playedCards']:
                    if card not in playedCardsOffSync:
                        if clients[id] == 0:
                            print(f'{clients[id]}   {card}')
                        sendMessage(conn, scs.TURNTEN_PLAY + ',' + scs.encodeStringMessage(card))
                playedCardsOffSync = copy.deepcopy(generalGameInfo['playedCards'])

            # Updates whose turn it is in the games
            if playerTurnOffSync != generalGameInfo['currentTurn']:
                if generalGameInfo['currentTurn'] >= len(clients):
                    generalGameInfo['currentTurn'] = 0
                
                sendMessage(conn, scs.TURN + ',' + str(generalGameInfo['currentTurn']) + "," + str(clients[id]))
                playerTurnOffSync = generalGameInfo['currentTurn']
                
            # Deals the client their cards
            if len(generalGameInfo['infoAboutPlayers']) > 0 and id not in syncClients['dealCards'][1] and syncClients['dealCards'][0]:
                sendMessage(conn, scs.GAME + ',' + scs.TURNTEN + ',' + str(len(clients)))

                hand = copy.deepcopy(generalGameInfo['infoAboutPlayers'][clients[id]]['hand'])
                minideck1 = copy.deepcopy(generalGameInfo['infoAboutPlayers'][clients[id]]['minideck1'])
                minideck2 = copy.deepcopy(generalGameInfo['infoAboutPlayers'][clients[id]]['minideck2'])
                minideck3 = copy.deepcopy(generalGameInfo['infoAboutPlayers'][clients[id]]['minideck3'])

                for theCard in hand:
                    sendMessage(conn, scs.TURNTEN_READ + ',' + scs.encodeStringMessage(theCard))

                for theCard in minideck1:
                    sendMessage(conn, scs.TURNTEN_MINIDECK1 + ',' + scs.encodeStringMessage(theCard))
                for theCard in minideck2:
                    sendMessage(conn, scs.TURNTEN_MINIDECK2 + ',' + scs.encodeStringMessage(theCard))
                for theCard in minideck3:
                    sendMessage(conn, scs.TURNTEN_MINIDECK3 + ',' + scs.encodeStringMessage(theCard))

                syncClients['dealCards'][1].append(id)

            # Sends the games stage to the client
            try:
                if generalGameInfo['infoAboutPlayers'][clients[id]]['stage'] != generalGameInfo['stage'] and generalGameInfo['infoAboutPlayers'][clients[id]]['wait']:
                    generalGameInfo['infoAboutPlayers'][clients[id]]['wait'] = False
                    generalGameInfo['infoAboutPlayers'][clients[id]]['stage'] = generalGameInfo['stage']
                    syncClients['changeStage'][1].append(id)
                    sendMessage(conn, scs.TURNTEN_STAGE + ',' + generalGameInfo['stage'])
            except:
                pass

    # Updates the server when the client disconnects
    infoAboutServer['numberOfPlayers'] -= 1
    try:
        generalGameInfo['infoAboutPlayers'].remove(clients[id])
        clients.remove(id)
    except:
        pass
    conn.close()

# Accepts new clients
def acceptClients(server):
    global syncClients
    global generalGameInfo
    global infoAboutServer

    server.settimeout(1.0)
    while not infoAboutServer['serverShutdown']:
        # If a client connects the server stores their connection and address
        try:
            conn, addr = server.accept()
        except socket.timeout:
            continue
        
        # Adds the clients id to the clients dictionary
        clients.update({infoAboutServer['clientId'] : infoAboutServer['clientId']})

        # Starts a thread that handles the connection to the client
        thread = threading.Thread(target=handle_client, args=(conn, addr, infoAboutServer['clientId']))
        thread.start()
        
        infoAboutServer['numberOfPlayers'] += 1
        infoAboutServer['clientId'] += 1

        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 3}")

# Starts the server
def start(ADDR, SERVER):
    global syncClients
    global generalGameInfo
    global infoAboutServer

    # Binds the server allowing connections to clients to happen
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)

    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")

    # Starts a thread that handles new connections
    thread = threading.Thread(target=acceptClients, args=(server,))
    thread.start()
    wait = 0

    # Handles the servers main functions
    while True:
        # Handles stuff related to the game turn ten
        if generalGameInfo['currentGame'] == scs.TURNTEN:
            # Starts a timer when all clients have finished the game
            if len(generalGameInfo['position']) == len(clients) and generalGameInfo['stage'] == scs.TURNTEN_END:
                generalGameInfo['stage'] = scs.TURNTEN_STAGE
                wait = time.time()

            # Displays the positions of all the clients for 3 seconds before shutting down the server
            if generalGameInfo['stage'] == scs.TURNTEN_STAGE and (time.time() - wait) > 3:
                infoAboutServer['serverShutdown'] = True

            # Syncs all the clients to the command "clearDeck"
            if syncClients['clearDeck'][0] and len(syncClients['clearDeck'][1]) == len(clients):
                generalGameInfo['playedCards'] = []
                syncClients['clearDeck'] = [False, []]

            # Syncs all the clients to the command "dealCards"
            if len(syncClients['dealCards'][1]) == len(clients) and syncClients['dealCards'][0]:
                syncClients['dealCards'] = [False, []]
                syncClients['switch'][0] = True

            # Syncs all the clients to the command "changeState"
            if len(syncClients['changeStage'][1]) == len(clients) and syncClients['changeStage'][0]:
                syncClients['changeStage'] = [False, [], False]

            # Syncs all the clients to the command "switch"
            if syncClients['switch'][0] and len(syncClients['switch'][1]) == len(clients):
                syncClients['switch'] = [False, []]

            # Syncs all the clients to the command "emptyDeck"
            if syncClients['emptyDeck'][0] and len(syncClients['emptyDeck'][1]) == len(clients):
                syncClients['emptyDeck'] = [False, []]
            
            # Syncs all the clients to the command "handNum"
            if syncClients['handNum'][0] and len(syncClients['handNum'][1]) == len(clients):
                syncClients['handNum'] = [False, []]

            # Creates the deck and all the hands and minidecks for all the clients
            if syncClients['dealCards'][0] and len(generalGameInfo['infoAboutPlayers']) == 0:
                i = 0
                # Makes sure the clients positions are consecutive
                for client in clients:
                    clients.update({client: i})
                    i += 1
                for i in range(len(clients)):
                    generalGameInfo['infoAboutPlayers'].append(copy.deepcopy(scs.turnTenInfo))
                
                generalGameInfo['deckOfCards'] = scs.createDeckOfCards(1)

                info = scs.dealing(generalGameInfo['deckOfCards'], 3, len(clients))
                generalGameInfo['deckOfCards'] = info[1]

                # Stores the hands of all the clients
                for p in range(len(generalGameInfo['infoAboutPlayers'])):
                    generalGameInfo['infoAboutPlayers'][p]['hand'] = copy.deepcopy(info[0][p])

                info = scs.dealing(generalGameInfo['deckOfCards'], 2, len(clients) * 3)

                # Stores the minidecks of all the players
                currentHand = 0
                for p in range(len(generalGameInfo['infoAboutPlayers'])): #players
                    generalGameInfo['infoAboutPlayers'][p]['minideck1'] = copy.deepcopy(info[0][currentHand])
                    generalGameInfo['infoAboutPlayers'][p]['minideck2'] = copy.deepcopy(info[0][currentHand + 1])
                    generalGameInfo['infoAboutPlayers'][p]['minideck3'] = copy.deepcopy(info[0][currentHand + 2])
                    currentHand += 3

                generalGameInfo['deckOfCards'] = info[1]

            # Changes the state of the server when all clients are ready eg all clients are waiting for middle game so the server then changes to middle game
            if syncClients['changeStage'][0] and syncClients['changeStage'][2]:
                waiting = 0
                for p in range(len(clients)):
                    if generalGameInfo['infoAboutPlayers'][p]['wait']:
                        waiting += 1
                if waiting == len(clients):
                    syncClients['changeStage'][2] = False
                    if generalGameInfo['stage'] == scs.TURNTEN_PRE:
                        generalGameInfo['stage'] = scs.TURNTEN_MIDDLE
                    elif generalGameInfo['stage'] == scs.TURNTEN_MIDDLE:
                        generalGameInfo['stage'] = scs.TURNTEN_END
                waiting = 0

            # If the deck is out of cards then the server tells the clients that
            if generalGameInfo['deckOfCards'] == 0:
                syncClients['emptyDeck'][0] = True
                
        # If the current turn exceeds the number of clients it resets back to zero
        if generalGameInfo['currentTurn'] >= len(clients):
            generalGameInfo.update({'currentTurn' : 0})

        # Shuts down the thread if the server is supposed to shut down
        if infoAboutServer['serverShutdown']:
            time.sleep(0.1)
            break

# Defines the port and server and start the server
def serverMain(IP):
    PORT = 5555
    SERVER = IP
    ADDR = (SERVER, PORT)

    print("[STARTING] Server is starting...")
    start(ADDR, SERVER)
    print("[CLOSING] Server shutting down...")