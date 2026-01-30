import pygame
from pygame import Surface
import pygame.sprite
import pygame.transform

class Monster(pygame.sprite.Sprite):
    def __init__(self,screen:Surface,mfont, img,x:int, y:int, 
                 move_x:int=1,  move_y:int=0,
                 width:int=40, height:int=40,
                 hp:int=1,
                 bullet_interval:int=-1):
        pygame.sprite.Sprite.__init__(self)
            
        self.screen = screen        
        self.mfont = mfont
        # img = pygame.image.load(f'{filename}').convert_alpha()
        self.image = pygame.transform.scale(img,(width,height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direction = 1
        self.move_x = move_x
        self.move_y = move_y
        self.hp = hp
        self.delay_counter = 0
        self.delay_bullet_counter = 0
        self.bullet_tick = pygame.time.get_ticks()
        self.bullet_tick_interval = bullet_interval  # 1 second interval for bullet firing
        
    def draw_hp(self):
        if self.hp > 1:        
            hp_text = self.mfont.render(f'HP: {self.hp}', True, (255, 0, 0))                
            hp_rect = hp_text.get_rect(center=(self.rect.centerx, self.rect.top - 10))
            
            temp_surface = pygame.Surface((hp_rect.width, hp_rect.height))
            temp_surface.fill((0,0,0))
            temp_surface.set_alpha(100)
            temp_surface.blit(hp_text,(0,0))
            self.screen.blit(temp_surface, hp_rect)
            
            
    def check_bullet(self):
        if self.bullet_tick_interval > 100:
            current_time = pygame.time.get_ticks()
            if current_time - self.bullet_tick > self.bullet_tick_interval:
                self.bullet_tick = current_time
                return True
        
        return False
            

    def update(self):
        self.draw_hp()
        self.rect.x += self.direction * self.move_x
        self.rect.y += self.direction * self.move_y  
        
        self.delay_counter += 1
        if abs(self.delay_counter) > 25:
            self.direction *= -1
            self.delay_counter *= -1
                  
        # self.rect.x += self.direction
        # self.delay_counter += 1
        # if abs(self.delay_counter) > self.move:
        #     self.direction *= -1
        #     self.delay_counter *= -1