import pygame
import os
import requests
import threading
import copy
import math

from network import *
from game import *
from server import *



pygame.font.init()

screen = pygame.display.set_mode((scs.SCREEN_WIDTH, scs.SCREEN_HEIGHT))
pygame.display.set_caption('Card With Friends')

FRAMERATE = 60


SCALE = scs.scaling(scs.CARD_HEIGHT)

# Loads the images for the cards
DECK_OF_CARDS_IMAGE = pygame.image.load(os.path.join('assets', 'deck_of_cards.png'))
DECK_OF_CARDS_SPRITE_SHEET = pygame.transform.scale(DECK_OF_CARDS_IMAGE.convert_alpha(), (SCALE * scs.CARD_WIDTH * 13, SCALE * scs.CARD_HEIGHT * 4))

CARD_BACKSIDE_IMAGE = pygame.image.load(os.path.join('assets', 'cardBackside.png'))
CARD_BACKSIDE = pygame.transform.scale(CARD_BACKSIDE_IMAGE.convert_alpha(), (SCALE * scs.CARD_WIDTH, SCALE * scs.CARD_HEIGHT))

# Creates a dictionary for the player to use for turnten
turnTenInfo = copy.deepcopy(scs.turnTenInfo)

# Defines all the buttons
buttonSizeMultipler = 0.7
menuButtons = [Button(scs.HOST, scs.SCREEN_WIDTH/2, 100, 100, 20, 0, buttonSizeMultipler, scs.START),
               Button(scs.JOIN, scs.SCREEN_WIDTH/2, 200, 100, 20, 1, buttonSizeMultipler, scs.START),
               Button(scs.SETTINGS, scs.SCREEN_WIDTH/2, 300, 100, 20, 2, buttonSizeMultipler, scs.START),
               Button(scs.QUIT, scs.SCREEN_WIDTH/2, 400, 100, 20, 3, buttonSizeMultipler, scs.START),
               Button(scs.CREDITS, scs.SCREEN_WIDTH/2, 600, 100, 20, 4, buttonSizeMultipler, scs.START),
               ]
multiplayerGameButtons = [Button(scs.TURNTEN, scs.SCREEN_WIDTH/2, 100, 100, 20, 0,buttonSizeMultipler, scs.GAME),
                          Button(scs.GOFISH, scs.SCREEN_WIDTH/2, 200, 100, 20, 1,buttonSizeMultipler, scs.GAME),
                          ]

# Returns the correct image depending on what card is inputted eg [3, 'spade'] returns the image for the 3 of spades
def chooseCard(card):
    value = card[0]
    suit = card[1]

    value -= 2

    if suit == 'spade':
        suit = 0
    elif suit == 'heart':
        suit = 1
    elif suit == 'club':
        suit = 2
    else:
        suit = 3

    return scs.spriteSheetToImage(value, suit, scs.CARD_WIDTH, scs.CARD_HEIGHT, DECK_OF_CARDS_SPRITE_SHEET)

# Draws the hand of the client and the number of cards the opponents have
def drawHand(turnTenInfo, otherPlayers, totalNumberOfPlayers, playableCards, glowRadius=7, distanceFromCenter=scs.CARD_HEIGHT*SCALE*1.5):
    spaceBetweenCards = scs.CARD_WIDTH * SCALE * 0.2
    spaceToBottomOfScreen = scs.CARD_HEIGHT * SCALE * 1.4

    # If a card in the hand is selected define the x coordinate so the selected card goes in the middle of the screen
    # otherwise as the middle of the screen minus half the hand so that the cards in the are centered on the screen
    if turnTenInfo['height'] == 1:
        x = scs.SCREEN_WIDTH / 2 - (scs.CARD_WIDTH * SCALE + spaceBetweenCards) * turnTenInfo['width'] - scs.CARD_WIDTH * SCALE / 2
    else: 
        x = scs.SCREEN_WIDTH / 2 - (scs.CARD_WIDTH * SCALE + spaceBetweenCards) * (len(turnTenInfo['hand']) - 1) / 2 - scs.CARD_WIDTH * SCALE / 2
    
    y = scs.SCREEN_HEIGHT - spaceToBottomOfScreen - scs.CARD_HEIGHT * SCALE

    # Draws a white frame around the current card that is being manipluated by actions in the hand
    if len(turnTenInfo['hand']) > 0:
        if turnTenInfo['height'] == 1:
            rectangle = pygame.Rect(scs.SCREEN_WIDTH / 2 - scs.CARD_WIDTH * SCALE / 2 - glowRadius * SCALE, y - glowRadius * SCALE, (glowRadius * 2 + scs.CARD_WIDTH) * SCALE, (glowRadius * 2 + scs.CARD_HEIGHT) * SCALE)
            pygame.draw.rect(screen, (255, 255, 255), rectangle)

    # Draws a pink fram around the cards that are selected for a swap
    for card in turnTenInfo['selectedCards']:
        for i in range(len(turnTenInfo['hand'])):
            if card == turnTenInfo['hand'][i]:
                rectangle = pygame.Rect(x - glowRadius * SCALE / 2 + (scs.CARD_WIDTH * SCALE + spaceBetweenCards) * i, y - glowRadius * SCALE / 2, (glowRadius + scs.CARD_WIDTH) * SCALE, (glowRadius + scs.CARD_HEIGHT) * SCALE)
                pygame.draw.rect(screen, (255, 0, 255), rectangle)

    # Draws the cards in the hand if there are cards in the hand
    if len(turnTenInfo['hand']) > 0:
        for card in turnTenInfo['hand']:
            cardImage = chooseCard(card)

            # If the card is playable it is 10 % bigger
            if card in playableCards:
                cardImage = pygame.transform.scale_by(cardImage, 1.1)
                differenceX = 0.1 * scs.CARD_WIDTH * SCALE / 2
                differenceY = 0.1 * scs.CARD_HEIGHT * SCALE / 2
            else:
                differenceX = 0
                differenceY = 0
            screen.blit(cardImage, (x - differenceX, y - differenceY))
            x += spaceBetweenCards + scs.CARD_WIDTH * SCALE

    x = scs.SCREEN_WIDTH / 2
    y = scs.SCREEN_HEIGHT / 2
    
    # Draws a backside of a card and the number of cards in that hand for every other player
    if len(otherPlayers) > 1:
        for player in range(len(otherPlayers)):
            if player != turnTenInfo['playerNumber']:
                deltaAngle = 2 * math.pi / totalNumberOfPlayers

                angle = math.pi / 2 + deltaAngle * (player - turnTenInfo['playerNumber'])

                xCoord = distanceFromCenter * math.cos(angle) + x
                yCoord = distanceFromCenter * math.sin(angle) + y

                rotate = math.degrees(math.pi / 2 - angle)

                cardImage = CARD_BACKSIDE

                # Rotates the card to point towards the center
                cardImage = pygame.transform.rotate(cardImage, rotate)
                screen.blit(cardImage, (xCoord - cardImage.get_width() / 2, yCoord - cardImage.get_height() / 2))

                # Draws the number that shows the number of cards in the hand
                font = pygame.font.SysFont('timesnewroman', 40 * scs.SCALE)
                text = font.render(str(otherPlayers[player]['numOfCards']), 1, (100,100,10))
                screen.blit(text, (xCoord - text.get_width() / 2, yCoord - text.get_height() / 2))


def drawMinidecks(turnTenInfo, otherPlayers, totalNumberOfPlayers, distance=scs.CARD_WIDTH*SCALE*1.5, distanceFromCenter=scs.CARD_HEIGHT*SCALE*2.7, glowRadius=7):
    # The midpoint of the screen
    x = scs.SCREEN_WIDTH / 2
    y = scs.SCREEN_HEIGHT / 2
    
    # START OF DOING THE DRAWING FOR MINIDECK1

    # Draws a white frame around minideck1 if it is the one the is currently manipulated for possible actions eg playing
    if turnTenInfo['height'] == 0 and turnTenInfo['width'] == 0:
        rectangle = pygame.Rect(x - (glowRadius + scs.CARD_WIDTH / 2) * SCALE - distance, y - (glowRadius + scs.CARD_HEIGHT / 2) * SCALE + distanceFromCenter, (glowRadius * 2 + scs.CARD_WIDTH) * SCALE, (glowRadius * 2 + scs.CARD_HEIGHT) * SCALE)
        pygame.draw.rect(screen, (255, 255, 255), rectangle)

    # Draws a pink frame around minideck1 if it is selected for a switch
    for card in turnTenInfo['selectedCards']:
        if card in turnTenInfo['minideck1']:
            rectangle = pygame.Rect(x - (glowRadius + scs.CARD_WIDTH) / 2 * SCALE - distance, y - (glowRadius + scs.CARD_HEIGHT) / 2 * SCALE + distanceFromCenter, (glowRadius + scs.CARD_WIDTH) * SCALE, (glowRadius + scs.CARD_HEIGHT) * SCALE)
            pygame.draw.rect(screen, (255, 0, 255), rectangle)

    # If there are 2 cards in minideck1 it draws the top card showing its value and suit
    if len(turnTenInfo['minideck1']) == 2:
        cardImage = chooseCard(turnTenInfo['minideck1'][1])
        screen.blit(cardImage, (x - scs.CARD_WIDTH / 2 * SCALE - distance, y - scs.CARD_HEIGHT / 2 * SCALE + distanceFromCenter))

    # If there is 1 card in minideck1 it draws the backside of a card
    elif len(turnTenInfo['minideck1']) == 1:
        screen.blit(CARD_BACKSIDE, (x - scs.CARD_WIDTH / 2 * SCALE - distance, y - scs.CARD_HEIGHT / 2 * SCALE + distanceFromCenter))

    # Draws minideck1 of all the other players
    if len(otherPlayers) > 1:
        for player in range(len(otherPlayers)):
            if player != turnTenInfo['playerNumber']:
                deltaAngle = 2 * math.pi / totalNumberOfPlayers

                angle = math.pi / 2 + deltaAngle * (player - turnTenInfo['playerNumber'])

                # Adds the offset for minideck1 from the middle of the screen
                xCoord = distanceFromCenter * math.cos(angle) + x
                yCoord = distanceFromCenter * math.sin(angle) + y
                
                # Adds the offset from the offset due to being an edge minideck
                xCoord += distance * math.cos(angle - math.pi / 2)
                yCoord += distance * math.sin(angle - math.pi / 2)

                # Rotates minideck1 to point towards the middle of the screen
                rotate = math.degrees(math.pi / 2 - angle)

                # If there are 2 cards in minideck1 it draws the top card showing its value and suit
                if len(otherPlayers[player]['minideck1']) >= 2:
                    cardImage = chooseCard(otherPlayers[player]['minideck1'][card])
                    cardImage = pygame.transform.rotate(cardImage, rotate)
                    screen.blit(cardImage, (xCoord - cardImage.get_width() / 2, yCoord - cardImage.get_height() / 2))

                # If there is 1 card in minideck1 it draws the backside of a card
                elif len(otherPlayers[player]['minideck1']) == 1:
                    cardImage = CARD_BACKSIDE
                    cardImage = pygame.transform.rotate(cardImage, rotate)
                    screen.blit(cardImage, (xCoord - cardImage.get_width() / 2, yCoord - cardImage.get_height() / 2))
    # END OF DOING THE DRAWING FOR MINIDECK1


    # START OF DOING THE DRAWING FOR MINIDECK2

    # Draws a white frame around minideck2 if it is the one the is currently manipulated for possible actions eg playing
    if turnTenInfo['height'] == 0 and turnTenInfo['width'] == 1:
        rectangle = pygame.Rect(x - (glowRadius + scs.CARD_WIDTH / 2) * SCALE, y - (glowRadius + scs.CARD_HEIGHT / 2) * SCALE + distanceFromCenter, (glowRadius * 2 + scs.CARD_WIDTH) * SCALE, (glowRadius * 2 + scs.CARD_HEIGHT) * SCALE)
        pygame.draw.rect(screen, (255, 255, 255), rectangle)

    # Draws a pink frame around minideck2 if it is selected for a switch
    for card in turnTenInfo['selectedCards']:
        if card in turnTenInfo['minideck2']:
            rectangle = pygame.Rect(x - (glowRadius + scs.CARD_WIDTH) / 2 * SCALE, y - (glowRadius + scs.CARD_HEIGHT) / 2 * SCALE + distanceFromCenter, (glowRadius + scs.CARD_WIDTH) * SCALE, (glowRadius + scs.CARD_HEIGHT) * SCALE)
            pygame.draw.rect(screen, (255, 0, 255), rectangle)

    # If there are 2 cards in minideck2 it draws the top card showing its value and suit
    if len(turnTenInfo['minideck2']) == 2:
        cardImage = chooseCard(turnTenInfo['minideck2'][1])
        screen.blit(cardImage, (x - scs.CARD_WIDTH / 2 * SCALE, y - scs.CARD_HEIGHT / 2 * SCALE + distanceFromCenter))

    # If there is 1 card in minideck3 it draws the backside of a card
    elif len(turnTenInfo['minideck2']) == 1:
        screen.blit(CARD_BACKSIDE, (x - scs.CARD_WIDTH / 2 * SCALE, y - scs.CARD_HEIGHT / 2 * SCALE + distanceFromCenter))

    # Draws minideck2 of all the other players
    if len(otherPlayers) > 1:
        for player in range(len(otherPlayers)):
            if player != turnTenInfo['playerNumber']:
                deltaAngle = 2 * math.pi / totalNumberOfPlayers

                angle = math.pi / 2 + deltaAngle * (player - turnTenInfo['playerNumber'])

                # Adds the offset for minideck2 from the middle of the screen
                xCoord = distanceFromCenter * math.cos(angle) + x
                yCoord = distanceFromCenter * math.sin(angle) + y

                # Rotates minideck2 to point towards the middle of the screen
                rotate = math.degrees(math.pi / 2 - angle)

                # If there are 2 cards in minideck2 it draws the top card showing its value and suit
                if len(otherPlayers[player]['minideck2']) >= 2:
                    cardImage = chooseCard(otherPlayers[player]['minideck2'][card])
                    cardImage = pygame.transform.rotate(cardImage, rotate)
                    screen.blit(cardImage, (xCoord - cardImage.get_width() / 2, yCoord - cardImage.get_height() / 2))

                # If there is 1 card in minideck2 it draws the backside of a card
                elif len(otherPlayers[player]['minideck2']) == 1:
                    cardImage = CARD_BACKSIDE
                    cardImage = pygame.transform.rotate(cardImage, rotate)
                    screen.blit(cardImage, (xCoord - cardImage.get_width() / 2, yCoord - cardImage.get_height() / 2))
    # END OF DOING THE DRAWING FOR MINIDECK2


    # START OF DOING THE DRAWING FOR MINIDECK3

    # Draws a white frame around minideck3 if it is the one the is currently manipulated for possible actions eg playing
    if turnTenInfo['height'] == 0 and turnTenInfo['width'] == 2:
        rectangle = pygame.Rect(x - (glowRadius + scs.CARD_WIDTH / 2) * SCALE + distance, y - (glowRadius + scs.CARD_HEIGHT / 2) * SCALE + distanceFromCenter, (glowRadius * 2 + scs.CARD_WIDTH) * SCALE, (glowRadius * 2 + scs.CARD_HEIGHT) * SCALE)
        pygame.draw.rect(screen, (255, 255, 255), rectangle)

    # Draws a pink frame around minideck3 if it is selected for a switch
    for card in turnTenInfo['selectedCards']:
        if card in turnTenInfo['minideck3']:
            rectangle = pygame.Rect(x - (glowRadius + scs.CARD_WIDTH) / 2 * SCALE + distance, y - (glowRadius + scs.CARD_HEIGHT) / 2 * SCALE + distanceFromCenter, (glowRadius + scs.CARD_WIDTH) * SCALE, (glowRadius + scs.CARD_HEIGHT) * SCALE)
            pygame.draw.rect(screen, (255, 0, 255), rectangle)

    # If there are 2 cards in minideck3 it draws the top card showing its value and suit
    if len(turnTenInfo['minideck3']) == 2:
        cardImage = chooseCard(turnTenInfo['minideck3'][1])
        screen.blit(cardImage, (x - scs.CARD_WIDTH / 2 * SCALE + distance, y - scs.CARD_HEIGHT / 2 * SCALE + distanceFromCenter))

    # If there is 1 card in minideck3 it draws the backside of a card
    elif len(turnTenInfo['minideck3']) == 1:
        screen.blit(CARD_BACKSIDE, (x - scs.CARD_WIDTH / 2 * SCALE + distance, y - scs.CARD_HEIGHT / 2 * SCALE + distanceFromCenter))

    # Draws minideck3 of all the other players
    if len(otherPlayers) > 1:
        for player in range(len(otherPlayers)):
            if player != turnTenInfo['playerNumber']:
                deltaAngle = 2 * math.pi / totalNumberOfPlayers

                angle = math.pi / 2 + deltaAngle * (player - turnTenInfo['playerNumber'])

                # Adds the offset for minideck3 from the middle of the screen
                xCoord = distanceFromCenter * math.cos(angle) + x
                yCoord = distanceFromCenter * math.sin(angle) + y
                
                # Adds the offset from the offset due to being an edge minideck
                xCoord -= distance * math.cos(angle - math.pi / 2)
                yCoord -= distance * math.sin(angle - math.pi / 2)

                # Rotates minideck3 to point towards the middle of the screen
                rotate = math.degrees(math.pi / 2 - angle)

                # If there are 2 cards in minideck3 it draws the top card showing its value and suit
                if len(otherPlayers[player]['minideck3']) >= 2:
                    cardImage = chooseCard(otherPlayers[player]['minideck3'][card])
                    cardImage = pygame.transform.rotate(cardImage, rotate)
                    screen.blit(cardImage, (xCoord - cardImage.get_width() / 2, yCoord - cardImage.get_height() / 2))

                # If there is 1 card in minideck3 it draws the backside of a card
                elif len(otherPlayers[player]['minideck3']) == 1:
                    cardImage = CARD_BACKSIDE
                    cardImage = pygame.transform.rotate(cardImage, rotate)
                    screen.blit(cardImage, (xCoord - cardImage.get_width() / 2, yCoord - cardImage.get_height() / 2))
    # END OF DOING THE DRAWING FOR MINIDECK3



def redrawScreen(screen, menu, playedCards, turnTenInfo, otherPlayers, totalNumberOfPlayers, playableCards, ip):
    # Fills the screen with a green colour
    screen.fill((0, 100, 0))

    # Draws the start menu buttons
    if menu == scs.START:
        for button in menuButtons:
            button.draw(screen)

    # Draws the multiplayer game buttons
    elif menu == scs.GAME:
        for button in multiplayerGameButtons:
            button.draw(screen)

    # Renders the host screen text: ip as well as additional information
    elif menu == scs.HOST:
        font = pygame.font.SysFont('timesnewroman', 40 * scs.SCALE)
        text = font.render(ip, 1, (255,255,255))
        screen.blit(text, (round(scs.SCREEN_WIDTH/2) - text.get_width()/2, round(scs.SCREEN_HEIGHT/2) - 2 * text.get_height()/2))
        if ip:
            text = font.render("Press F3 to continue!", 1, (255,255,255))
            screen.blit(text, (round(scs.SCREEN_WIDTH/2) - text.get_width()/2, round(scs.SCREEN_HEIGHT/2) + text.get_height()/2))

    # Renders the join screen text: The ip that has been inputted
    elif menu == scs.JOIN:
        font = pygame.font.SysFont('timesnewroman', 40 * scs.SCALE)
        text = font.render(ip, 1, (255,255,255))
        screen.blit(text, (round(scs.SCREEN_WIDTH/2) - text.get_width()/2, round(scs.SCREEN_HEIGHT/2) - text.get_height()/2))

    # Renders the graphics for the game turn ten
    elif menu == scs.TURNTEN:
        # Draws the last played card on screen
        if len(playedCards) > 0:
            card = chooseCard(playedCards[len(playedCards) - 1])
            screen.blit(card, (scs.SCREEN_WIDTH / 2 + scs.centerX(card), scs.SCREEN_HEIGHT / 2 + scs.centerY(card)))

        # If the game has ended, it shows the postion the player finished in
        if turnTenInfo['stage'] == scs.TURNTEN_END:
            font = pygame.font.SysFont('timesnewroman', 40 * scs.SCALE)
            text = font.render('YOUR POSITION: ' + str(turnTenInfo['position']), 1, (255,255,255))
            screen.blit(text, (round(scs.SCREEN_WIDTH/2) - text.get_width()/2, scs.SCREEN_HEIGHT / 2 - 2.4 * text.get_height()))


        # Draws all of the players hand on screen
        drawHand(turnTenInfo, otherPlayers, totalNumberOfPlayers, playableCards)

        # Draws áll of the players minidecks
        drawMinidecks(turnTenInfo, otherPlayers, totalNumberOfPlayers)

    pygame.display.update()

def main():
    clock = pygame.time.Clock()

    # The cards that have been played so far
    playedCards = []

    # The currently playable cards
    playableCards = []

    ip = '192.168.0.127'
    ipText = ip
    serverStarted = False
    netWorkCreated = False

    menu = scs.START

    gameStarted = False

    currentTurn = 0
    totalNumberOfPlayers = 0

    otherPlayers = []

    # Controls
    left = False
    right = False
    up = False
    down = False

    host = False
    run = True
    while run:
        try:
            pass
        except:
            pass
        clock.tick(FRAMERATE)

        if netWorkCreated:
            msg = n.retrieveMessage()
            if msg:
                decodedMsg = scs.decodeStringMessage(msg)

                if decodedMsg[0] == scs.GAME:
                    decodedMsg.pop(0)
                    menu = decodedMsg[0]
                    if len(decodedMsg) == 2:
                        otherPlayers = []
                        totalNumberOfPlayers = int(decodedMsg[1])
                        for i in range(totalNumberOfPlayers):
                            otherPlayers.append(copy.deepcopy(scs.otherPlayersTurnTen))
                            otherPlayers[i]['minideck1'].append(scs.TURNTEN_PLACEHOLDER_CARD)
                            otherPlayers[i]['minideck1'].append(scs.TURNTEN_PLACEHOLDER_CARD)
                            otherPlayers[i]['minideck2'].append(scs.TURNTEN_PLACEHOLDER_CARD)
                            otherPlayers[i]['minideck2'].append(scs.TURNTEN_PLACEHOLDER_CARD)
                            otherPlayers[i]['minideck3'].append(scs.TURNTEN_PLACEHOLDER_CARD)
                            otherPlayers[i]['minideck3'].append(scs.TURNTEN_PLACEHOLDER_CARD)

                elif decodedMsg[0] == scs.TURN:
                    decodedMsg.pop(0)
                    decodedMsg[0] = int(decodedMsg[0])
                    decodedMsg[1] = int(decodedMsg[1])
                    currentTurn = decodedMsg[0]
                    turnTenInfo['playerNumber'] = int(decodedMsg[1])

                elif decodedMsg[0] == scs.POSITION:
                    turnTenInfo['position'] = int(decodedMsg[1])
                
                elif menu == scs.TURNTEN:
                    if decodedMsg[0] == scs.TURNTEN_READ:
                        decodedMsg.pop(0)
                        decodedMsg[0] = int(decodedMsg[0])
                        turnTenInfo['hand'].append(decodedMsg)

                    elif decodedMsg[0] == scs.TURNTEN_MINIDECK1:
                        decodedMsg.pop(0)
                        decodedMsg[0] = int(decodedMsg[0])
                        turnTenInfo['minideck1'].append(decodedMsg)

                    elif decodedMsg[0] == scs.TURNTEN_MINIDECK2:
                        decodedMsg.pop(0)
                        decodedMsg[0] = int(decodedMsg[0])
                        turnTenInfo['minideck2'].append(decodedMsg)

                    elif decodedMsg[0] == scs.TURNTEN_MINIDECK3:
                        decodedMsg.pop(0)
                        decodedMsg[0] = int(decodedMsg[0])
                        turnTenInfo['minideck3'].append(decodedMsg)

                    elif decodedMsg[0] == scs.TURNTEN_PLAY:
                        decodedMsg.pop(0)
                        decodedMsg[0] = int(decodedMsg[0])
                        print(decodedMsg)
                        playedCards.append(decodedMsg)

                    elif decodedMsg[0] == scs.TURNTEN_CLEARDECK:
                        playedCards = []

                    elif decodedMsg[0] == scs.TURNTEN_STAGE:
                        turnTenInfo['wait'] = False
                        turnTenInfo['stage'] = decodedMsg[1]

                    elif decodedMsg[0] == scs.TURNTEN_SWITCH:
                        decodedMsg.pop(0)
                        player = int(decodedMsg[0])
                        decodedMsg.pop(0)

                        if decodedMsg[0] == 'minideck1':
                            if decodedMsg[2] == scs.TURNTEN_NOCARD:
                                try:
                                    otherPlayers[player]['minideck1'].pop(int(decodedMsg[1]))
                                except:
                                    pass
                            else:
                                otherPlayers[player]['minideck1'][int(decodedMsg[1])] = [int(decodedMsg[2]), decodedMsg[3]]
                        elif decodedMsg[0] == 'minideck2':
                            if decodedMsg[2] == scs.TURNTEN_NOCARD:
                                try:
                                    otherPlayers[player]['minideck2'].pop(int(decodedMsg[1]))
                                except:
                                    pass
                            else:
                                otherPlayers[player]['minideck2'][int(decodedMsg[1])] = [int(decodedMsg[2]), decodedMsg[3]]
                        elif decodedMsg[0] == 'minideck3':
                            if decodedMsg[2] == scs.TURNTEN_NOCARD:
                                try:
                                    otherPlayers[player]['minideck3'].pop(int(decodedMsg[1]))
                                except:
                                    pass
                            else:
                                otherPlayers[player]['minideck3'][int(decodedMsg[1])] = [int(decodedMsg[2]), decodedMsg[3]]
                        elif decodedMsg[0] == 'hand':
                            otherPlayers[player]['numOfCards'] = int(decodedMsg[3])

                    elif decodedMsg == scs.TURNTEN_EMPTYDECK:
                        turnTenInfo['emptyDeck'] = True

        if menu == scs.HOST and serverStarted == False:
            ip = socket.gethostbyname(socket.gethostname())
            thread = threading.Thread(target=serverMain, args=(ip,))
            thread.start()
            ipText = 'Your IP: ' + ip

            host = True

            serverStarted = True

            n = Network(ip)
            n.connect()
            netWorkCreated = True
        
        if (menu in scs.GAMES) and gameStarted == False and host:
            n.sendMessage(scs.GAME + ',' + menu)
            gameStarted = True

        if menu == scs.TURNTEN:
            # A fail safe in case the player plays the first or last card or the dev switches players
            if turnTenInfo['width'] < 0 and turnTenInfo['height'] == 1:
                turnTenInfo['width'] = 0
            if turnTenInfo['width'] >= len(turnTenInfo['hand']) and turnTenInfo['height'] == 1:
                turnTenInfo['width'] = len(turnTenInfo['hand']) - 1
            if turnTenInfo['width'] < 0 and turnTenInfo['height'] == 0:
                turnTenInfo['width'] = 0
            if turnTenInfo['width'] > 2 and turnTenInfo['height'] == 0:
                turnTenInfo['width'] = 2

            if turnTenInfo['stage'] == scs.TURNTEN_MIDDLE and turnTenInfo['wait'] == False:
                if len(turnTenInfo['hand']) == 0:
                    # The Minidecks get force selected if the hand is empty
                    turnTenInfo['height'] = 0

                # Checks which cards are eligable to be played
                playableCards = []
                if len(turnTenInfo['hand']) > 0:
                    for card in turnTenInfo['hand']:
                        if len(playedCards) > 0:
                            if card[0] >= playedCards[len(playedCards) - 1][0] or card[0] == 2 or card[0] == 10:
                                playableCards.append(card)
                        else:
                            playableCards = copy.deepcopy(turnTenInfo['hand'])
                elif len(turnTenInfo['minideck1']) == 2 or len(turnTenInfo['minideck2']) == 2 or len(turnTenInfo['minideck3']) == 2:
                    if len(playedCards) > 0:
                        if len(turnTenInfo['minideck1']) == 2:
                            if turnTenInfo['minideck1'][1][0] >= playedCards[len(playedCards) - 1][0] or turnTenInfo['minideck1'][1][0] == 2 or turnTenInfo['minideck1'][1][0] == 10:
                                playableCards.append(turnTenInfo['minideck1'][1])
                        if len(turnTenInfo['minideck2']) == 2:
                            if turnTenInfo['minideck2'][1][0] >= playedCards[len(playedCards) - 1][0] or turnTenInfo['minideck2'][1][0] == 2 or turnTenInfo['minideck2'][1][0] == 10:
                                playableCards.append(turnTenInfo['minideck2'][1])
                        if len(turnTenInfo['minideck3']) == 2:
                            if turnTenInfo['minideck3'][1][0] >= playedCards[len(playedCards) - 1][0] or turnTenInfo['minideck3'][1][0] == 2 or turnTenInfo['minideck3'][1][0] == 10:
                                playableCards.append(turnTenInfo['minideck3'][1])
                    else:
                        if len(turnTenInfo['minideck1']) == 2:
                            playableCards.append(turnTenInfo['minideck1'][1])
                        if len(turnTenInfo['minideck2']) == 2:
                            playableCards.append(turnTenInfo['minideck2'][1])
                        if len(turnTenInfo['minideck3']) == 2:
                            playableCards.append(turnTenInfo['minideck3'][1])
                else:
                    if len(playedCards) > 0:
                        if len(turnTenInfo['minideck1']) == 1:
                            if turnTenInfo['minideck1'][0][0] >= playedCards[len(playedCards) - 1][0] or turnTenInfo['minideck1'][0][0] == 2 or turnTenInfo['minideck1'][0][0] == 10:
                                playableCards.append(turnTenInfo['minideck1'][0])
                        if len(turnTenInfo['minideck2']) == 1:
                            if turnTenInfo['minideck2'][0][0] >= playedCards[len(playedCards) - 1][0] or turnTenInfo['minideck2'][0][0] == 2 or turnTenInfo['minideck2'][0][0] == 10:
                                playableCards.append(turnTenInfo['minideck2'][0])
                        if len(turnTenInfo['minideck3']) == 1:
                            if turnTenInfo['minideck3'][0][0] >= playedCards[len(playedCards) - 1][0] or turnTenInfo['minideck3'][0][0] == 2 or turnTenInfo['minideck3'][0][0] == 10:
                                playableCards.append(turnTenInfo['minideck3'][0])
                    else:
                        if len(turnTenInfo['minideck1']) == 1:
                            playableCards.append(turnTenInfo['minideck1'][0])
                        if len(turnTenInfo['minideck2']) == 1:
                            playableCards.append(turnTenInfo['minideck2'][0])
                        if len(turnTenInfo['minideck3']) == 1:
                            playableCards.append(turnTenInfo['minideck3'][0])


                if currentTurn == turnTenInfo['playerNumber'] and turnTenInfo['takeAChance'] == 2:
                    for card in playedCards:
                        turnTenInfo['hand'].append(card)
                    n.sendMessage(scs.TURNTEN_PICKUPPILE)
                    n.sendMessage(scs.TURN)
                    turnTenInfo['takeAChance'] = 0


                # If the player has no cards left enter the end stage of not being part of the game by skipping their turn
                if len(turnTenInfo['hand']) == 0 and len(turnTenInfo['minideck1']) == 0 and len(turnTenInfo['minideck2']) == 0 and len(turnTenInfo['minideck3']) == 0:
                    if turnTenInfo['stage'] != scs.TURNTEN_END:
                        turnTenInfo['stage'] = scs.TURNTEN_END
                        n.sendMessage(scs.TURNTEN_STAGE + ',' + scs.TURNTEN_END)
                        turnTenInfo['wait'] = True

            if turnTenInfo['stage'] == scs.TURNTEN_END and currentTurn == turnTenInfo['playerNumber']:
                n.sendMessage(scs.TURN)
                currentTurn += 1


        for event in pygame.event.get():
            if event.type == pygame.QUIT or menu == scs.QUIT:
                try:
                    n.sendMessage(scs.SERVER_SHUTDOWN_MESSAGE)
                    del n
                except:
                    pass
                
                run = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if menu == scs.START:
                    for button in menuButtons:
                        if button.clicked(pygame.mouse.get_pos()):
                            menu = button.output

                if menu == scs.GAME:
                    for button in multiplayerGameButtons:
                        if button.clicked(pygame.mouse.get_pos()):
                            menu = button.output

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_F4:
                    n.sendMessage(scs.SERVER_SHUTDOWN_MESSAGE)
                    del n
                    menu = scs.START
                    netWorkCreated = False
                    playedCards = []
                    turnTenInfo['width'] = 0
                    turnTenInfo['height'] = 1
                    turnTenInfo['hand'] = []

                if event.key == pygame.K_ESCAPE:
                    if menu in (scs.JOIN, scs.HOST, scs.SETTINGS, scs.CREDITS):
                        menu = scs.START
                        try:
                            netWorkCreated = False
                            serverStarted = False
                            netWorkCreated = False
                            gameStarted = False
                            currentTurn = 0
                            totalNumberOfPlayers = 0
                            otherPlayers = []
                            playedCards = []
                            del n
                        except:
                            pass

                    elif menu == scs.GAME:
                        if serverStarted:
                            menu = scs.HOST
                        else:
                            menu = scs.JOIN

                    elif menu in scs.GAMES:
                        menu = scs.GAME
                
                if menu == scs.HOST:
                    if event.key == pygame.K_F3:
                        menu = scs.GAME

                if menu == scs.JOIN:
                    if event.key == pygame.K_0:
                        ip += '0'
                    if event.key == pygame.K_1:
                        ip += '1'
                    if event.key == pygame.K_2:
                        ip += '2'
                    if event.key == pygame.K_3:
                        ip += '3'
                    if event.key == pygame.K_4:
                        ip += '4'
                    if event.key == pygame.K_5:
                        ip += '5'
                    if event.key == pygame.K_6:
                        ip += '6'
                    if event.key == pygame.K_7:
                        ip += '7'
                    if event.key == pygame.K_8:
                        ip += '8'
                    if event.key == pygame.K_9:
                        ip += '9'
                    if event.key == pygame.K_PERIOD:
                        ip += '.'
                    if event.key == pygame.K_BACKSPACE:
                        ip = ip[:-1]

                    ipText = ip

                    if event.key == pygame.K_RETURN:
                        if netWorkCreated == False:
                            n = Network(ip)
                        netWorkCreated = True
                        n.connect()

                if menu == scs.TURNTEN:
                    if event.key == pygame.K_LEFT:
                        left = True
                    if event.key == pygame.K_RIGHT:
                        right = True
                    if event.key == pygame.K_UP:
                        up = True
                    if event.key == pygame.K_DOWN:
                        down = True

            if event.type == pygame.KEYUP:
                if menu == scs.TURNTEN:
                    if event.key == pygame.K_LEFT:
                        left = False
                    if event.key == pygame.K_RIGHT:
                        right = False
                    if event.key == pygame.K_UP:
                        up = False
                    if event.key == pygame.K_DOWN:
                        down = False

            if event.type == pygame.KEYDOWN:
                # TurnTen the game
                if menu == scs.TURNTEN:
                    # Lets the player control which card is selected
                    if left and turnTenInfo['width'] > 0:
                        turnTenInfo['width'] -= 1
                    if right and turnTenInfo['width'] < len(turnTenInfo['hand']) - 1 and turnTenInfo['height'] == 1 or right and turnTenInfo['width'] < 2 and turnTenInfo['height'] == 0:
                        turnTenInfo['width'] += 1
                    if up and turnTenInfo['height'] < 1:
                        turnTenInfo['height'] += 1
                    if down and turnTenInfo['height'] > 0:
                        turnTenInfo['height'] -= 1

                    # Controls for the pregame of turn ten eg switching cards
                    if turnTenInfo['stage'] == scs.TURNTEN_PRE and turnTenInfo['wait'] == False:
                        if event.key == pygame.K_LSHIFT:
                            if turnTenInfo['height'] == 1:
                                card = turnTenInfo['hand'][turnTenInfo['width']]
                                if card in turnTenInfo['selectedCards']:
                                    turnTenInfo['selectedCards'].remove(card)
                                elif len(turnTenInfo['selectedCards']) < 2:
                                    turnTenInfo['selectedCards'].append(turnTenInfo['hand'][turnTenInfo['width']])
                            else:
                                if turnTenInfo['width'] == 0:
                                    card = turnTenInfo['minideck1'][len(turnTenInfo['minideck1']) - 1]
                                    if card in turnTenInfo['selectedCards']:
                                        turnTenInfo['selectedCards'].remove(card)
                                    elif len(turnTenInfo['selectedCards']) < 2:
                                        turnTenInfo['selectedCards'].append(turnTenInfo['minideck1'][len(turnTenInfo['minideck1']) - 1])

                                elif turnTenInfo['width'] == 1:
                                    card = turnTenInfo['minideck2'][len(turnTenInfo['minideck2']) - 1]
                                    if card in turnTenInfo['selectedCards']:
                                        turnTenInfo['selectedCards'].remove(card)
                                    elif len(turnTenInfo['selectedCards']) < 2:
                                        turnTenInfo['selectedCards'].append(turnTenInfo['minideck2'][len(turnTenInfo['minideck2']) - 1])

                                else:
                                    card = turnTenInfo['minideck3'][len(turnTenInfo['minideck3']) - 1]
                                    if card in turnTenInfo['selectedCards']:
                                        turnTenInfo['selectedCards'].remove(card)
                                    elif len(turnTenInfo['selectedCards']) < 2:
                                        turnTenInfo['selectedCards'].append(turnTenInfo['minideck3'][len(turnTenInfo['minideck3']) - 1])

                        if event.key == pygame.K_SPACE:
                            if len(turnTenInfo['selectedCards']) == 2:
                                n.sendMessage(scs.TURNTEN_SWITCH + ',' + scs.encodeStringMessage(turnTenInfo['selectedCards'][0]) + ',' + scs.encodeStringMessage(turnTenInfo['selectedCards'][1]))

                                cards = []
                                # Checks the position of the two cards that need to be switched and stores them as cards = [[x1, y1], [x2, y2]]
                                for i in range(2):
                                    if turnTenInfo['selectedCards'][i] in turnTenInfo['hand']:
                                        cards.append([turnTenInfo['hand'].index(turnTenInfo['selectedCards'][i]), 1])
                                    elif turnTenInfo['selectedCards'][i] == turnTenInfo['minideck1'][len(turnTenInfo['minideck1']) - 1]:
                                        cards.append([0, 0])
                                    elif turnTenInfo['selectedCards'][i] == turnTenInfo['minideck2'][len(turnTenInfo['minideck2']) - 1]:
                                        cards.append([1, 0])
                                    elif turnTenInfo['selectedCards'][i] == turnTenInfo['minideck3'][len(turnTenInfo['minideck3']) - 1]:
                                        cards.append([2, 0])

                                

                                if cards[0][1] == 1:  # First selected card is from 'hand'
                                    turnTenInfo['hand'][cards[0][0]] = turnTenInfo['selectedCards'][1]
                                else:  # First selected card is from a minideck
                                    if cards[0][0] == 0:
                                        turnTenInfo['minideck1'][len(turnTenInfo['minideck1']) - 1] = turnTenInfo['selectedCards'][1]
                                    elif cards[0][0] == 1:
                                        turnTenInfo['minideck2'][len(turnTenInfo['minideck2']) - 1] = turnTenInfo['selectedCards'][1]
                                    elif cards[0][0] == 2:
                                        turnTenInfo['minideck3'][len(turnTenInfo['minideck3']) - 1] = turnTenInfo['selectedCards'][1]

                                if cards[1][1] == 1:  # Second selected card is from 'hand'
                                    turnTenInfo['hand'][cards[1][0]] = turnTenInfo['selectedCards'][0]
                                else:  # Second selected card is from a minideck
                                    if cards[1][0] == 0:
                                        turnTenInfo['minideck1'][len(turnTenInfo['minideck1']) - 1] = turnTenInfo['selectedCards'][0]
                                    elif cards[1][0] == 1:
                                        turnTenInfo['minideck2'][len(turnTenInfo['minideck2']) - 1] = turnTenInfo['selectedCards'][0]
                                    elif cards[1][0] == 2:
                                        turnTenInfo['minideck3'][len(turnTenInfo['minideck3']) - 1] = turnTenInfo['selectedCards'][0]

                                cards = []
                                turnTenInfo['selectedCards'] = []

                        # Continue the game to the first waiting stage for this client
                        if event.key == pygame.K_c and turnTenInfo['wait'] == False:
                            turnTenInfo['wait'] = True
                            turnTenInfo['selectedCards'] = []
                            n.sendMessage(scs.TURNTEN_STAGE + ',' + scs.TURNTEN_WAIT)

                    
                    if turnTenInfo['stage'] == scs.TURNTEN_MIDDLE and turnTenInfo['wait'] == False:
                        hand = True
                        if len(playableCards) == 0 and turnTenInfo['takeAChance'] == 0 and turnTenInfo['emptyDeck'] == False:
                            if len(turnTenInfo['hand']) > 0:
                                turnTenInfo['takeAChance'] = 1
                        elif len(turnTenInfo['hand']) > 0:
                            hand = False
                            if event.key == pygame.K_SPACE and currentTurn == turnTenInfo['playerNumber'] and len(playableCards) > 0:
                                if turnTenInfo['hand'][turnTenInfo['width']] in playableCards and turnTenInfo['height'] == 1:
                                    n.sendMessage(scs.TURNTEN_PLAY + ',' + scs.encodeStringMessage(turnTenInfo['hand'][turnTenInfo['width']]))
                                    if turnTenInfo['hand'][turnTenInfo['width']][0] != 2 and turnTenInfo['hand'][turnTenInfo['width']][0] != 10:
                                        n.sendMessage(scs.TURN)

                                    elif turnTenInfo['hand'][turnTenInfo['width']][0] == 10:
                                        n.sendMessage(scs.TURNTEN_CLEARDECK)
                                        
                                    turnTenInfo['hand'].pop(turnTenInfo['width'])
                                    turnTenInfo['takeAChance'] = 0
                                    if len(turnTenInfo['hand']) < 3 and turnTenInfo['emptyDeck'] == False:
                                        n.sendMessage(scs.TURNTEN_PICKUPCARD)
                                    
                            elif event.key == pygame.K_SPACE and currentTurn == turnTenInfo['playerNumber'] and turnTenInfo['takeAChance'] == 1:
                                n.sendMessage(scs.TURNTEN_PICKUPCARD)
                                turnTenInfo['takeAChance'] = 2

                        # If the hand has been activated do not play from the minidecks
                        if len(turnTenInfo['hand']) == 0 and hand:

                            # If there are cards in any of the minidecks, let the player play one of those cards
                            if len(turnTenInfo['minideck1']) != 0 or len(turnTenInfo['minideck2']) != 0 or len(turnTenInfo['minideck3']) != 0:

                                if event.key == pygame.K_SPACE:

                                    # If any of the minidecks has 2 cards force them to play the visible second card of a minideck
                                    if len(turnTenInfo['minideck1']) == 2 or len(turnTenInfo['minideck2']) == 2 or len(turnTenInfo['minideck3']) == 2:

                                        # If the first card is selected let the player try to play that card
                                        if len(turnTenInfo['minideck1']) == 2 and turnTenInfo['width'] == 0:
                                            card = turnTenInfo['minideck1'][1]

                                            # If the card is playable let the player play that card
                                            if card in playableCards:
                                                turnTenInfo['minideck1'].pop(1)
                                                n.sendMessage(scs.TURNTEN_MINIDECK1 + ',' + scs.encodeStringMessage(card))
                                                if card[0] == 10:
                                                    n.sendMessage(scs.TURNTEN_CLEARDECK)
                                                if card[0] != 2 and card[0] != 10:
                                                    n.sendMessage(scs.TURN)

                                            # If the card is not playable, add the card and the deck to the players hand
                                            else:
                                                turnTenInfo['minideck1'].pop(1)
                                                turnTenInfo['hand'].append(card)
                                                for theCard in playedCards:
                                                    turnTenInfo['hand'].append(theCard)
                                                n.sendMessage(scs.TURNTEN_MINIDECK1 + ',' + scs.encodeStringMessage(card))
                                                n.sendMessage(scs.TURNTEN_PICKUPPILE)
                                                n.sendMessage(scs.TURN)

                                        
                                        elif len(turnTenInfo['minideck2']) == 2 and turnTenInfo['width'] == 1:
                                            card = turnTenInfo['minideck2'][1]

                                            # If the card is playable let the player play that card
                                            if card in playableCards:
                                                turnTenInfo['minideck2'].pop(1)
                                                n.sendMessage(scs.TURNTEN_MINIDECK2 + ',' + scs.encodeStringMessage(card))
                                                if card[0] == 10:
                                                    n.sendMessage(scs.TURNTEN_CLEARDECK)
                                                if card[0] != 2 and card[0] != 10:
                                                    n.sendMessage(scs.TURN)

                                            # If the card is not playable, add the card and the deck to the players hand
                                            else:
                                                turnTenInfo['minideck2'].pop(1)
                                                turnTenInfo['hand'].append(card)
                                                for theCard in playedCards:
                                                    turnTenInfo['hand'].append(theCard)
                                                n.sendMessage(scs.TURNTEN_MINIDECK1 + ',' + scs.encodeStringMessage(card))
                                                n.sendMessage(scs.TURNTEN_PICKUPPILE)
                                                n.sendMessage(scs.TURN)

                                        elif len(turnTenInfo['minideck3']) == 2 and turnTenInfo['width'] == 2:
                                            card = turnTenInfo['minideck3'][1]

                                            # If the card is playable let the player play that card
                                            if card in playableCards:
                                                turnTenInfo['minideck3'].pop(1)
                                                n.sendMessage(scs.TURNTEN_MINIDECK3 + ',' + scs.encodeStringMessage(card))
                                                if card[0] == 10:
                                                    n.sendMessage(scs.TURNTEN_CLEARDECK)
                                                if card[0] != 2 and card[0] != 10:
                                                    n.sendMessage(scs.TURN)

                                            # If the card is not playable, add the card and the deck to the players hand
                                            else:
                                                turnTenInfo['minideck3'].pop(1)
                                                turnTenInfo['hand'].append(card)
                                                for theCard in playedCards:
                                                    turnTenInfo['hand'].append(theCard)
                                                n.sendMessage(scs.TURNTEN_MINIDECK3 + ',' + scs.encodeStringMessage(card))
                                                n.sendMessage(scs.TURNTEN_PICKUPPILE)
                                                n.sendMessage(scs.TURN)

                                    # If all of the minidecks have at most 1 card force the player to play a hidden card
                                    else:
                                        if turnTenInfo['width'] == 0:
                                            if len(turnTenInfo['minideck1']) == 1:
                                                card = turnTenInfo['minideck1'][0]
                                                if card in playableCards:
                                                    turnTenInfo['minideck1'].pop(0)
                                                    n.sendMessage(scs.TURNTEN_MINIDECK1 + ',' + scs.encodeStringMessage(card))
                                                    n.sendMessage(scs.TURN)
                                                else:
                                                    turnTenInfo['minideck1'].pop(0)
                                                    turnTenInfo['hand'].append(card)
                                                    for theCard in playedCards:
                                                        turnTenInfo['hand'].append(theCard)
                                                    n.sendMessage(scs.TURNTEN_MINIDECK1 + ',' + scs.encodeStringMessage(card))
                                                    n.sendMessage(scs.TURNTEN_PICKUPPILE)
                                                    n.sendMessage(scs.TURN)

                                        elif turnTenInfo['width'] == 1:
                                            if len(turnTenInfo['minideck2']) == 1:
                                                card = turnTenInfo['minideck2'][0]
                                                if card in playableCards:
                                                    turnTenInfo['minideck2'].pop(0)
                                                    n.sendMessage(scs.TURNTEN_MINIDECK2 + ',' + scs.encodeStringMessage(card))
                                                    n.sendMessage(scs.TURN)
                                                else:
                                                    turnTenInfo['minideck2'].pop(0)
                                                    turnTenInfo['hand'].append(card)
                                                    for theCard in playedCards:
                                                        turnTenInfo['hand'].append(theCard)
                                                    n.sendMessage(scs.TURNTEN_MINIDECK2 + ',' + scs.encodeStringMessage(card))
                                                    n.sendMessage(scs.TURNTEN_PICKUPPILE)
                                                    n.sendMessage(scs.TURN)

                                        elif turnTenInfo['width'] == 2:
                                            if len(turnTenInfo['minideck3']) == 1:
                                                card = turnTenInfo['minideck3'][0]
                                                if card in playableCards:
                                                    turnTenInfo['minideck3'].pop(0)
                                                    n.sendMessage(scs.TURNTEN_MINIDECK3 + ',' + scs.encodeStringMessage(card))
                                                    n.sendMessage(scs.TURN)
                                                else:
                                                    turnTenInfo['minideck3'].pop(0)
                                                    turnTenInfo['hand'].append(card)
                                                    for theCard in playedCards:
                                                        turnTenInfo['hand'].append(theCard)
                                                    n.sendMessage(scs.TURNTEN_MINIDECK3 + ',' + scs.encodeStringMessage(card))
                                                    n.sendMessage(scs.TURNTEN_PICKUPPILE)
                                                    n.sendMessage(scs.TURN)


        
        redrawScreen(screen, menu, playedCards, turnTenInfo, otherPlayers, totalNumberOfPlayers, playableCards, ipText)

    pygame.quit

if __name__ == '__main__':
    main()

