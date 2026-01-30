import pygame
from pygame import Surface
import pygame.sprite
import pygame.transform

class ExitDoor(pygame.sprite.Sprite):
    def __init__(self,screen:Surface, img,x:int, y:int, next_level:int,width:int=60, height:int=60):
        pygame.sprite.Sprite.__init__(self)
                    
        self.screen = screen        
        # img = pygame.image.load(f'{filename}').convert_alpha()
        self.image_src = pygame.transform.scale(img,(width,height))
        self.image = self.image_src
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.next_level = next_level
        
        
    def update(self):
        pass