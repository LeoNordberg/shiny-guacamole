import sys
import gc
import pickle
import random
import pygame

START = '!START'
JOIN = '!JOIN'
HOST = '!HOST'
GAME = '!GAME'
SETTINGS = '!SETTINGS'
QUIT = '!QUIT'
CREDITS = '!CREDITS'

TURNTEN = '!TURNTEN'
GOFISH = '!GOFISH'
GAMES = (GOFISH, TURNTEN)

TURNTEN_WAIT = '!WAIT'
TURNTEN_CLEARDECK = '!CLEARDECK'
TURNTEN_DEAL = '!DEAL'
TURNTEN_PRE = '!PRE'
TURNTEN_MIDDLE = '!MIDDLE'
TURNTEN_END = '!END'
TURNTEN_PICKUPCARD = '!PICKUPCARD'
TURNTEN_CHANCE = '!CHANCE'
TURNTEN_PLAY = '!PLAY'
TURNTEN_READ = '!READ'
TURNTEN_PICKUPPILE = '!PICKUPPILE'
TURNTEN_MINIDECK1 = '!MINIDECK1'
TURNTEN_MINIDECK2 = '!MINIDECK2'
TURNTEN_MINIDECK3 = '!MINIDECK3'
TURNTEN_STAGE = '!STAGE'
TURNTEN_SWITCH = '!SWITCH'
TURNTEN_PLACEHOLDER = '!PLACEHOLDER'
TURNTEN_EMPTYDECK = '!EMPTYDECK'
TURNTEN_PLACEHOLDER_CARD = [14, 'spade']
TURNTEN_NOCARD = '!NOCARD'

POSITION = '!POSTION'
TURN = '!TURN'

FORMAT = 'utf_8'
HEADER = 64
DISCONNECT_MESSAGE = "!DISCONNECT"
DEAL_CARDS_MESSAGE = "!DEAL"
SERVER_SHUTDOWN_MESSAGE = "!SERVER_SHUTDOWN"
GAME_START_MESSAGE = "!START_GAME"

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900

PERCENT_SCALE = 0.15
SCALE = 2

CARD_WIDTH = 51
CARD_HEIGHT = 79

BUTTON_WIDTH = 100
BUTTON_HEIGHT = 20

#  Info about the player when they're playing turn ten
turnTenInfo = {'minideck1' : [],
               'minideck2' : [],
               'minideck3' : [],
               'hand' : [],
               'height' : 1,
               'width' : 0,
               'takeAChance' : 0,
               'stage' : TURNTEN_PRE,             # pre, middle, end
               'wait' : False,
               'selectedCards' : [],
               'emptyDeck' : False,
               'position' : 0,
               'playerNumber' : 0
               } 

# Relevent info about the other players in turn ten
otherPlayersTurnTen = {'minideck1' : [],
                       'minideck2' : [],
                       'minideck3' : [],
                       'numOfCards' : 0
                       }

# Returns the scaling number for a certain number
def scaling(height):
    return (PERCENT_SCALE * SCREEN_HEIGHT) / height

# Rotates the image and sends the delta x and delta y to center the image
def rotateImage(image, degrees):
    pygame.transform.rotate(image, degrees)
    x = - image.get_width() / 2
    y = - image.get_height() / 2
    return [image, x, y]

# Gives the offset of x to center an image
def centerX(image):
    return - image.get_width() / 2

# Gives the offset of y to center an image
def centerY(image):
    return - image.get_height() / 2

# Outputs a single image from a spritesheet
def spriteSheetToImage(x, y, width, height, spriteSheet):
    theScale = scaling(height)

    # Creates a surface thats the size of the specified size
    image = pygame.Surface((width * theScale, height * theScale)).convert_alpha()

    # Takes the specified image from the spritesheet and puts it on the image eg a card from the card sheet
    image.blit(spriteSheet, (0, 0), (x * width * theScale, y * height * theScale, width * theScale, height * theScale))
    return image

# Gets the total memory usage of nested list, python objects and so on.
# NOT IN USE
def deep_getsizeof(obj, seen=None):
    """Recursively calculates the total memory footprint of an object, including its attributes."""
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = sys.getsizeof(obj)  # Base size of object

    # Recursively add sizes of referenced objects
    for referent in gc.get_referents(obj):
        size += deep_getsizeof(referent, seen)

    return size

# Separates strings by commas and adds them into a list eg 'a,b,c' -> ['a', 'b', 'c']
def decodeStringMessage(text):
    try:
        text = text.split(",")
    except:
        text = [text]
    return text

# Turns lists, numbers and strings into strings separeted by a comma eg [123, 'b', 'heart'] -> '123,b,heart'
def encodeStringMessage(message):
    msg = ''

    for i in range(len(message)):
        msg += str(message[i])
        if i != len(message) - 1:
            msg += ','

    return msg

# Creates a deck of cards in multiples of 52 cards
def createDeckOfCards(numberOfDecks):
    value = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
    suit = ('spade', 'heart', 'club', 'diamond')
    
    currentValue = 0
    currentSuit = 0
    currentDeck = 0

    deckOfCards = []

    while currentDeck < numberOfDecks:
        card = [value[currentValue], suit[currentSuit]]
        deckOfCards.append(card)
        currentValue += 1
        if currentValue == 13:
            currentValue = 0
            currentSuit += 1

        if currentSuit == 4:
            currentSuit = 0
            currentDeck += 1

    return deckOfCards

# Deals the correct number of cards to the correct numbers of players from the deck
def dealing(deckOfCards, numberOfCards, numberOfHands):
    hands = []
    # Adds the correct number of players into the players list
    while len(hands) < numberOfHands:
        hands.append([])

    count = 0

    # Deals a random cards from the deck to the players going from player 1 to player n and stops when the last player has the correct number of cards which means all of the players have the correct number of cards
    while len(hands[numberOfHands - 1]) < numberOfCards:

        card = deckOfCards[random.randint(0, len(deckOfCards) - 1)]

        current_player = hands[count % numberOfHands]
        current_player.append(card)

        # Removes the card that was just dealt so that it cannot be dealt again
        deckOfCards.remove(card)

        count += 1

    return [hands, deckOfCards]

# Checks if the client has performed the appropriate action
def checkClient(id, syncClients, action):
    if id not in syncClients[action] and syncClients[action][0]:
        return True
    else:
        return False