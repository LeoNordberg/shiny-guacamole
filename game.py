import pygame
import os

import serverClientShares as scs

SCALE = scs.scaling(scs.BUTTON_HEIGHT)
MENU_BUTTONS_IMAGE = pygame.image.load(os.path.join('assets', 'mainMenuButtons.png'))
MENU_BUTTONS_SPRITE_SHEET = pygame.transform.scale(MENU_BUTTONS_IMAGE, (SCALE * 100, SCALE * 20 * 5))

GAME_BUTTONS_IMAGE = pygame.image.load(os.path.join('assets', 'multiplayerGameButtons.png'))
GAME_BUTTONS_SPRITE_SHEET = pygame.transform.scale(GAME_BUTTONS_IMAGE, (SCALE * 100, SCALE * 20 * 5))

# Creates a button class
class Button:
    def __init__(self, output, x, y, width, height, whichButton, size, menu):
        self.output = output
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.whichButton = whichButton
        self.size = size
        self.menu = menu

    # Draws the button in respect to the specified values
    def draw(self, screen):
        SCALE = scs.scaling(self.height)
        if self.menu == scs.START:
            screen.blit(pygame.transform.scale(scs.spriteSheetToImage(0, self.whichButton, self.width, self.height, MENU_BUTTONS_SPRITE_SHEET), (self.size * SCALE * self.width, self.size * SCALE * self.height)), (self.x - self.width/2 * SCALE * self.size, self.y - self.height/2 * SCALE * self.size))
        elif self.menu == scs.GAME:
            screen.blit(pygame.transform.scale(scs.spriteSheetToImage(0, self.whichButton, self.width, self.height, GAME_BUTTONS_SPRITE_SHEET), (self.size * SCALE * self.width, self.size * SCALE * self.height)), (self.x - self.width/2 * SCALE * self.size, self.y - self.height/2 * SCALE * self.size))

    # Checks if the button was clicked
    def clicked(self, pos):
        SCALE = scs.scaling(self.height)
        x1 = pos[0]
        y1 = pos[1]
        if self.x - self.width/2 * SCALE * self.size <= x1 <= self.x + self.width/2 * SCALE * self.size and self.y - self.height/2 * SCALE * self.size <= y1 <= self.y + self.height/2 * SCALE * self.size:
            return True
        else:
            return False