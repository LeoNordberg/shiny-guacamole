import pygame
import os
import random

SCREEN_WIDTH = 1680
SCREEN_HEIGHT = 850

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

FRAMERATE = 60

SCALE = 3

DECK_OF_CARDS_IMAGE = pygame.image.load(os.path.join('assets', 'deck_of_cards.png'))
DECK_OF_CARDS_SPRITE_SHEET = pygame.transform.scale(DECK_OF_CARDS_IMAGE.convert_alpha(), (SCALE * 51 * 13, SCALE * 79 * 4))

def chooseCard(value, suit):
    value -= 2

    if suit == 'spade':
        suit = 0
    elif suit == 'heart':
        suit = 1
    elif suit == 'club':
        suit = 2
    else:
        suit = 3

    image = pygame.Surface((51 * SCALE, 79 * SCALE)).convert_alpha()
    image.blit(DECK_OF_CARDS_SPRITE_SHEET, (0, 0), (value * 51 * SCALE, suit * 79 * SCALE, 51 * SCALE, 79 * SCALE))
    return image

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

def dealing(deckOfCards, numberOfCards, numberOfPlayers):
    players = []
    # Adds the correct number of players into the players list
    while len(players) < numberOfPlayers:
        players.append([])

    count = 0

    # Deals a random cards from the deck to the players going from player 1 to player n and stops when the last player has the correct number of cards which means all of the players have the correct number of cards
    while len(players[numberOfPlayers - 1]) < numberOfCards:

        card = deckOfCards[random.randint(0, len(deckOfCards) - 1)]

        current_player = players[count % numberOfPlayers]
        current_player.append(card)

        deckOfCards.remove(card) # Removes the card that was just dealt so that it cannot be dealt again

        count += 1

    return [players, deckOfCards]

def drawHand(players, whichPlayer, selectedCard, glowRadius=5):
    player = players[whichPlayer]
    spaceBetweenCards = 10
    spaceToBottomOfScreen = 20

    x = (SCREEN_WIDTH - len(player) * SCALE * 51 - (len(player) - 1) * spaceBetweenCards * SCALE) / 2
    y = SCREEN_HEIGHT - spaceToBottomOfScreen - SCALE * 79

    if len(player) > 0:
        rectangle = pygame.Rect(x + (SCALE * (51 + spaceBetweenCards)) * selectedCard - glowRadius * SCALE, y - glowRadius * SCALE, SCALE * (51 + glowRadius * 2), SCALE * (79 + glowRadius * 2))
        pygame.draw.rect(screen, (255, 255, 255), rectangle)

    count = 0
    while count < len(player):
        screen.blit(chooseCard(player[count][0], player[count][1]), (x, y))
        x += SCALE * (51 + spaceBetweenCards)
        count += 1


def poker():
    ...


def main():
    clock = pygame.time.Clock()

    # Creates a deck of cards with n number of complete single decks e.g 52, 104, 156 cards etc
    deckOfCards = createDeckOfCards(1)

    # Returns data about the players hands and what cards are left in the deck
    infoDealing = dealing(deckOfCards, 3, 4)
    players = infoDealing[0]
    deckOfCards = infoDealing[1]

    # The cards that have been played so far
    playedCards = []

    # The current selected card in the list
    selectedCard = 0
    player = 0

    run = True
    while run:
        # The player of this instance
        

        clock.tick(FRAMERATE)

        screen.fill((0, 100, 0))

        # Draws the players hand on screen
        drawHand(players, player, selectedCard)


        # Draws the last played card on screen
        if len(playedCards) > 0:
            screen.blit(chooseCard(playedCards[len(playedCards) - 1][0], playedCards[len(playedCards) - 1][1]), ((SCREEN_WIDTH - 51 * SCALE) / 2, (SCREEN_HEIGHT - 79 * SCALE) / 2))




        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False


            if event.type == pygame.KEYDOWN:
                # Lets the player control which card is selected
                if event.key == pygame.K_LEFT and selectedCard > 0:
                    selectedCard -= 1
                if event.key == pygame.K_RIGHT and selectedCard < len(players[player]) - 1:
                    selectedCard += 1

                if event.key == pygame.K_DOWN and player > 0:
                    player -= 1
                if event.key == pygame.K_UP and player < len(players) - 1:
                    player += 1

                # Lets the player play the selected card
                if event.key == pygame.K_SPACE:
                    playedCards.append(players[player][selectedCard])
                    players[player].pop(selectedCard)

        # A fail safe in case the player plays the first or last card and the dev switches players
        if selectedCard < 0:
            selectedCard = 0
        if selectedCard >= len(players[player]):
            selectedCard = len(players[player]) - 1
        

        pygame.display.update()


    pygame.quit

if __name__ == '__main__':
    main()