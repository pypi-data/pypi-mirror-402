

import os
try:
    import pygame
except:
    os.system('pip install pygame')
    import pygame
import random
from pygame.event import Event
from pygame.surface import *

from codingnow.game.spacewar.drawBg import *
from codingnow.game.spacewar.player import *
from codingnow.game.spacewar.drawMsg import *
from codingnow.game.spacewar.enemy import *

class SpaceWar():
    player:Player = None
    message:DrawMsg = None
    event_func_p = None
    enemys = {}
    enemy_gen_time = 0
    backgrounds = {}
    images_dict = {}    
	
    path = {
        'img' : None,
        'snd' : None,
        }
    
    def __init__(self,screen:Surface) -> None:
        self.screen = screen
        self.player = None
        self.group_enemy = pygame.sprite.Group()
        self.message = DrawMsg(self.screen)
        self.drawbg = DrawBg(self.screen)
        pass

    def set_folder(self, images:str=None, sounds:str=None):
        self.path['img'] = images
        self.path['snd'] = sounds
        
    def get_folder_img(self, filename):
        
        if filename is None:
            return None
        
        if self.path['img'] is None:
            return filename

        return f"./{self.path['img']}/{filename}"

    def get_folder_snd(self, filename):
        
        if filename is None:
            return None
        
        if self.path['snd'] is None:
            return filename

        return f"./{self.path['snd']}/{filename}"
        
    def event_func(event:Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                # print('aaaa')
                pass
                
    def check_quit(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
            if self.event_func_p is not None:
                self.event_func_p(event)
        return True
    
    def set_msg_score(self, x=10,y=10, color = (0,0,0), text = '점수 : '):
        self.message.set_msg_score(x,y,color,text)
        
    def set_msg_level(self, x=10,y=50, color = (0,0,0), text = '레벨 : '):
        self.message.set_msg_level(x,y,color,text)
        
    def set_msg_weapon(self, x=10,y=90, color = (0,0,0), text = '레벨 : '):
        self.message.set_msg_weapon(x,y,color,text)
        
    def set_msg_hp(self, x=10,y=130, color = (0,0,0), text = 'HP : '):
        self.message.set_msg_hp(x,y,color,text)
          
######################################################################################
    def add_bg_image(self, level, filename):
        filename = self.get_folder_img(filename)
        img = pygame.image.load(f'{filename}').convert_alpha()
        img = pygame.transform.scale(img, (self.screen.get_width(), self.screen.get_height()))
        self.backgrounds[level] = img
        
        # rect = pygame.Rect(0,0,self.screen.get_width(),self.screen.get_height())
        # img = DrawBg(self.screen,filename,rect)
        # self.img_bg = img
######################################################################################        
    def add_enemy(self,level,
                  filename,
                  width,
                  height,
                  hp=100,
                  speed=1,
                  delay = 1000,
                  angle = 0,
                  flip=False,
                  
                  weapon_filename=None, 
                  weapon_width=60,
                  weapon_height=50,
                  weapon_damage = 10, 
                  weapon_speed = 1, 
                  weapon_dealy = 1000,
                  weapon_flip = True,
                  
                  item_filename=None, 
                  item_width=60,
                  item_height=50,
                  item_hp = 0,
                  item_weapon_filename = None,
                  item_weapon_width=60,
                  item_weapon_height=50,
                  item_weapon_damage = 0, 
                  item_weapon_delay = 0, 
                  item_weapon_speed = 1, 
                  ):
        
        if level not in self.enemys:
            self.enemys[level] = {}
        # print(self.enemys)
        key = len(self.enemys[level])
        
        filename = self.get_folder_img(filename)
        if filename in self.images_dict:
            img = self.images_dict[filename]
        else:            
            img = pygame.image.load(f'{filename}').convert_alpha()
            self.images_dict[filename] = img
            
        img = pygame.transform.scale(img, (width, height))
        if flip:
            img = pygame.transform.flip(img,True,False)            
        if angle!=0:
            img = pygame.transform.rotate(img,angle)
            
        weapon_filename = self.get_folder_img(weapon_filename)
        if weapon_filename is not None:
            if weapon_filename in self.images_dict:
                img_w = self.images_dict[weapon_filename]
            else:            
                img_w = pygame.image.load(f'{weapon_filename}').convert_alpha()
                self.images_dict[weapon_filename] = img_w
                
            img_w = pygame.transform.scale(img_w, (weapon_width, weapon_height))
            if weapon_flip:
                img_w = pygame.transform.flip(img_w,True,False)  
        else:
            img_w = None
            
        item_filename = self.get_folder_img(item_filename)
        if item_filename is not None:
            
            if item_filename in self.images_dict:
                img_i = self.images_dict[item_filename]
            else:            
                img_i = pygame.image.load(f'{item_filename}').convert_alpha()
                self.images_dict[item_filename] = img_i
                
            img_i = pygame.transform.scale(img_i, (item_width, item_height))
            # if item_flip:
            #     img_i = pygame.transform.flip(img_i,True,False)  
        else:
            img_i = None
            
        item_weapon_filename = self.get_folder_img(item_weapon_filename)
        if item_weapon_filename is not None:
            
            if item_weapon_filename in self.images_dict:
                item_img_weapon = self.images_dict[item_weapon_filename]
            else:            
                item_img_weapon = pygame.image.load(f'{item_weapon_filename}').convert_alpha()
                self.images_dict[item_weapon_filename] = item_img_weapon
                
            item_img_weapon = pygame.transform.scale(item_img_weapon, (item_weapon_width, item_weapon_height))
            # if item_flip:
            #     img_i = pygame.transform.flip(img_i,True,False)  
        else:
            item_img_weapon = None
        item_weapon_speed *= -1
        self.enemys[level][key] = {'img':img, 
                                   'hp':hp,
                                   'speed':speed,
                                   'delay':delay,
                                   'delay_tick':pygame.time.get_ticks() + delay,
                                   
                                   'w_img':img_w, 
                                   'w_damage':weapon_damage,
                                   'w_speed':weapon_speed,
                                   'w_delay':weapon_dealy,
                                   
                                   'i_img':img_i, 
                                   'i_weapon_filename':item_weapon_filename,
                                   'i_weapon_img':item_img_weapon,
                                   'i_weapon_damage':item_weapon_damage,
                                   'i_weapon_delay':item_weapon_delay,
                                   'i_weapon_speed':item_weapon_speed,
                                   'i_hp':item_hp
                                   }
        
        
        # enem = Enemy(self.screen,filename,width,height,hp,speed)
        # self.enemys[level][key] = enem
        
######################################################################################
    def create_player(self,filename=None, hp = 1000, x=-1,y=-1,width=60,height=50, angle = 0, flip = False):
        
        filename = self.get_folder_img(filename)
        rect = pygame.Rect(x,y,width,height)
        
        if x==-1:
            rect.right = self.screen.get_width()-width
        if y == -1:
            rect.centery = self.screen.get_height()/2
            
        self.player = Player(self,self.screen,filename,rect,hp,angle, flip)
        return self.player
    
    def set_player(self,filename, hp = 500, x=-1,y=-1,width=100,height=90, angle = 0, flip = False):
        filename = self.get_folder_img(filename)
        rect = pygame.Rect(x,y,width,height)
        
        if x==-1:
            rect.right = self.screen.get_width()-width
        if y == -1:
            rect.centery = self.screen.get_height()/2
            
        self.player = Player(self,self.screen,filename,rect,hp,angle, flip)
        return self.player
    
######################################################################################
    def get_curr_level(self):
        if self.player is None:
            return 1
        else:
            return self.player.level
        
    def gen_enemy(self):
        level = self.get_curr_level()
            
        if level in self.enemys:
            for key in self.enemys[level]:                
                val = self.enemys[level][key]
                if val['delay_tick'] < pygame.time.get_ticks():
                    val['delay_tick'] = pygame.time.get_ticks() + val['delay']
                    img = Enemy(self.screen,
                                player=self.player,
                                
                                img=val['img'],
                                hp=val['hp'],
                                speed=val['speed'],
                                
                                w_img=val['w_img'],
                                w_damage=val['w_damage'],
                                w_speed=val['w_speed'],
                                w_delay=val['w_delay'],
                                
                                i_img=val['i_img'],
                                i_hp=val['i_hp'],
                                
                                i_weapon_filename=val['i_weapon_filename'],
                                i_weapon_img=val['i_weapon_img'],
                                i_weapon_damage=val['i_weapon_damage'],
                                i_weapon_delay=val['i_weapon_delay'],
                                i_weapon_speed=val['i_weapon_speed'],
                                )
                    img.rect.right = 1
                    img.rect.y = random.randint(img.rect.height, self.screen.get_height()-img.rect.height)
                    self.group_enemy.add(img)
                
    def draw_bg(self):
        level = self.get_curr_level()            
        if level in self.backgrounds:
            self.drawbg.draw(self.backgrounds[level])
        else:
            if 1 in self.backgrounds:
                self.drawbg.draw(self.backgrounds[1])
            
    def draw_message(self):
        
        if self.message is not None:
            if self.message.draw(self.player):
                self.group_enemy.empty()
                self.game_restart()
            
    def draw_player(self):
        if self.player is not None and self.player.game_over==False:
            if self.player.check_levelup():
                if self.message is not None:
                    self.message.set_status_msg(f'Level Up!!')
                
            self.player.draw(self.group_enemy)
                
    def draw_enemy(self):
        if (self.player is not None) and self.player.game_over:
            return
        self.gen_enemy()
        self.group_enemy.update()
        self.group_enemy.draw(self.screen)
        
    def game_restart(self):
        if self.player is not None:
            self.player.reset()
            self.group_enemy.empty()
            self.enemy_gen_time = pygame.time.get_ticks() + 1000
    
    def draw(self):
        self.draw_bg()
        
        self.draw_message()
        
        self.draw_enemy()
        self.draw_player()
            