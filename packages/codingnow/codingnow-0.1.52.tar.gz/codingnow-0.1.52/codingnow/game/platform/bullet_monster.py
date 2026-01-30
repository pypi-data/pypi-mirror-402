import pygame
from pygame import *
import pygame.time

from codingnow.game.platform.monster import *

class BulletMonster(pygame.sprite.Sprite):
	
    def __init__(self,screen:Surface,img,monster:Monster):
        pygame.sprite.Sprite.__init__(self)
        self.screen = screen
        self.direction = monster.direction*2
        if self.direction < 0:
            self.direction *= -1
        # img = pygame.image.load(f'{filename}').convert_alpha()
        width = img.get_width()/2
        height = img.get_height()/2
        self.image_src = pygame.transform.scale(img,(width,height))
        self.image = self.image_src
        self.hp = 1
        self.rect = self.image.get_rect()
        self.rect.centerx = monster.rect.centerx
        self.rect.centery = monster.rect.centery
		 

    def update(self):
        self.rect.y += self.direction            
        if self.rect.y < 0 or self.rect.top > self.screen.get_height():
            self.kill()