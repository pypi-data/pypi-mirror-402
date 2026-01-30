import pygame
from pygame.locals import *
from pygame import Surface

from codingnow.game.spacewar.enemy import *
from codingnow.game.spacewar.weapon import *
from codingnow.game.spacewar.items import *

class Player():
	score=0
	hp=100
	level = 1
	level_pre = 1
	
	is_start = True
	speed = 2
	weapon_img = None
	weapon_filename = None
	weapon_damage = 0
	weapon_speed = 0
	weapon_delay = 0

	weapon_def_img = None
	weapon_def_filename = None
	weapon_def_damage = 0
	weapon_def_speed = 0
	weapon_def_delay = 0
	
	weapon_list = {}
	
	group_weapon = pygame.sprite.Group()
	group_items = pygame.sprite.Group()
	
	game_over = False
	
	images = []
	score_set_level = {}
	speed_set_level = {}
	
	def __init__(self,parent, screen:Surface,filename, rect:pygame.Rect, hp = 100,angle=0, flip=False):
		self.parent = parent
		self.screen = screen
		self.hp = hp
		self.hp_start = hp
		
		filename = self.parent.get_folder_img(filename)
		if filename is None:
			img = self.draw_airplane(rect.width, rect.height)
			angle = 90
		else:
			img = pygame.image.load(f'{filename}').convert_alpha()
			img = pygame.transform.scale(img, (rect.width, rect.height))
		
		if flip:
			img = pygame.transform.flip(img,True,False)
			
		if angle!=0:
			img = pygame.transform.rotate(img,angle)
			
		self.images = [img]
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.x = rect.x
		self.rect.y = rect.y
		self.sx = rect.x
		self.sy = rect.y
		self.weapon_tick = 0
		
		self.shield_tick = 0
		self.shield_on = False
		
		self.snd_dic = {
			'shoot':None,
			'hit':None,
			'item':None,
			'shock':None,
			'game_over':None,
		}
		
		self.mfont = pygame.font.SysFont('malgungothic', 20)
		
	def set_level_next(self, level:int, score:int):
		self.score_set_level[level] = score
		
	def set_level_speed(self, level:int, speed:int):
		self.speed_set_level[level] = speed
				
	def draw_airplane(self, width: int = 100, height: int = 100):
		temp_surface = pygame.Surface((width, height), pygame.SRCALPHA)

		# 색상
		GRAY = (180, 180, 180)
		DARK_GRAY = (80, 80, 80)
		BLUE = (0, 100, 255)

		# 중심 기준점
		center_x = width // 2
		center_y = height // 2

		# 동체 (몸통): 중앙 세로 사각형
		body_width = width * 0.2
		body_height = height * 0.8
		body_rect = pygame.Rect(center_x - body_width // 2, center_y - body_height // 2, body_width, body_height)
		pygame.draw.rect(temp_surface, GRAY, body_rect)

		# 앞부분 (기수): 삼각형
		nose_tip = (center_x, center_y - body_height // 2 - height * 0.1)
		nose_left = (center_x - body_width // 2, center_y - body_height // 2)
		nose_right = (center_x + body_width // 2, center_y - body_height // 2)
		pygame.draw.polygon(temp_surface, DARK_GRAY, [nose_tip, nose_left, nose_right])

		# 날개: 양쪽으로 뻗는 삼각형
		wing_left = [(center_x - body_width // 2, center_y),
					(center_x - width * 0.45, center_y + height * 0.1),
					(center_x - body_width // 2, center_y + height * 0.2)]
		wing_right = [(center_x + body_width // 2, center_y),
					(center_x + width * 0.45, center_y + height * 0.1),
					(center_x + body_width // 2, center_y + height * 0.2)]
		pygame.draw.polygon(temp_surface, BLUE, wing_left)
		pygame.draw.polygon(temp_surface, BLUE, wing_right)

		# 꼬리날개: 상단 삼각형
		tail_center = (center_x, center_y + body_height // 2)
		tail_left = (center_x - width * 0.1, tail_center[1] + height * 0.15)
		tail_right = (center_x + width * 0.1, tail_center[1] + height * 0.15)
		pygame.draw.polygon(temp_surface, DARK_GRAY, [tail_center, tail_left, tail_right])

		return temp_surface

	def set_imgage(self, level,filename,width,height,angle=0, flip=False):
		if level < 1:
			return
		
		while True:
			length = len(self.images)
			if level <= length:
				break
			self.images.append(None)
		# print('setimg : ',self.images)
		filename = self.parent.get_folder_img(filename)
		if filename is None:
			img = self.draw_airplane(width, height)
			angle = 90
		else:
			img = pygame.image.load(f'{filename}').convert_alpha()
			img = pygame.transform.scale(img, (width, height))
			
		if flip:
			img = pygame.transform.flip(img,True,False)
			
		if angle!=0:
			img = pygame.transform.rotate(img,angle)
			
		self.images[level-1] = img
		
	def get_img(self, level):
		try:
			img = self.images[level-1]
			if img is not None:
				self.image = self.images[level-1]
				rect = self.image.get_rect()
				self.rect.width = rect.width
				self.rect.height = rect.height
		except Exception as ex:
			pass
		
	def reset(self):
		self.score=0
		self.level = 1
		self.level_pre = 1
		self.get_img(self.level)
		self.hp=self.hp_start
		self.rect.x = self.sx
		self.rect.y = self.sy
		
		self.weapon_img = self.weapon_def_img
		self.weapon_damage = self.weapon_def_damage
		self.weapon_speed = self.weapon_def_speed
		self.weapon_delay = self.weapon_def_delay
		self.group_weapon.empty()
		self.group_items.empty()
		
		self.game_over = False
		
	def check_levelup(self):
		if self.level > self.level_pre:
			self.level_pre = self.level
			self.get_img(self.level)
			return True
		
		self.level_pre = self.level
		return False
	
	def set_snd_shoot(self,filename):
		filename = self.parent.get_folder_snd(filename)
		self.snd_dic['shoot'] = pygame.mixer.Sound(filename)
		
	def set_snd_item(self,filename):
		filename = self.parent.get_folder_snd(filename)
		self.snd_dic['item'] = pygame.mixer.Sound(filename)
		
	def set_snd_hit(self,filename):
		filename = self.parent.get_folder_snd(filename)
		self.snd_dic['hit'] = pygame.mixer.Sound(filename)
		
	def set_snd_game_over(self,filename):
		filename = self.parent.get_folder_snd(filename)
		self.snd_dic['game_over'] = pygame.mixer.Sound(filename)
		
	def set_snd_shock(self,filename):
		filename = self.parent.get_folder_snd(filename)
		self.snd_dic['shock'] = pygame.mixer.Sound(filename)
		
######################################################################################
	def set_weapon(self, filename, width, height, damage,speed,delay, flip=False):
		filename = self.parent.get_folder_img(filename)
		img = pygame.image.load(f'{filename}').convert_alpha()
		img = pygame.transform.scale(img, (width, height))
		if flip:
			img = pygame.transform.flip(img,True,False)
			
		self.weapon_img = img
		self.weapon_filename = filename
		self.weapon_damage = damage
		self.weapon_speed = speed*-1
		self.weapon_delay = delay
		
		self.weapon_def_filename = self.weapon_filename
		self.weapon_def_img = self.weapon_img
		self.weapon_def_damage = self.weapon_damage
		self.weapon_def_speed = self.weapon_speed
		self.weapon_def_delay = self.weapon_delay
		
		self.set_weapon_list(filename,img,damage,speed,delay)
		
	def set_weapon_list(self,filename,img,damage,speed,delay):
		filename = self.parent.get_folder_img(filename)
		if filename not in self.weapon_list:
			self.weapon_list[filename] = {
				'filename':None,
				'img':None,
				'damage':0,
				'speed':0,
				'delay':0,
				}
		self.weapon_list[filename]['filename'] = filename
		self.weapon_list[filename]['img'] = img
		self.weapon_list[filename]['damage'] = damage
		self.weapon_list[filename]['speed'] = speed
		self.weapon_list[filename]['delay'] = delay
			
######################################################################################
	def key_pressed(self):
		key_press = pygame.key.get_pressed()
		
		if key_press[pygame.K_UP]:
			self.rect.y -= self.speed
			
		if key_press[pygame.K_DOWN]:
			self.rect.y += self.speed
							
		if key_press[pygame.K_LEFT]:
			self.rect.x -= self.speed
			
		if key_press[pygame.K_RIGHT]:
			self.rect.x += self.speed
			
		if key_press[pygame.K_SPACE]:
			if self.weapon_img is not None:
				if pygame.time.get_ticks() - self.weapon_tick > self.weapon_delay:
					self.weapon_tick = pygame.time.get_ticks()
					cx = self.rect.centerx
					cy = self.rect.centery
					weapon = Weapon(self.screen, self.weapon_img,cx,cy,self.weapon_damage, self.weapon_speed)
					self.group_weapon.add(weapon)
					if self.snd_dic['shoot'] is not None:
						self.snd_dic['shoot'].play()
				
	def draw_shield(self):
		
		if self.shield_on:
			self.shield_tick = pygame.time.get_ticks()
			self.shield_on = False
			
		if self.shield_tick > 0:
			ellip = pygame.time.get_ticks() - self.shield_tick
			if ellip < 500:
				temp_surface = pygame.Surface(self.image.get_size())
				temp_surface.fill((255, 0, 255))
				temp_surface.blit(self.image, (0, 0))
				temp_surface.set_alpha(80)
				self.screen.blit(temp_surface, self.rect)
			else:
				self.shield_tick = 0
				
	def draw_items(self):
		rect_pre = None
		key_press = pygame.key.get_pressed()
		for i, weapon in enumerate(self.weapon_list):	
			if key_press[pygame.K_1+i]:				
				self.weapon_filename = self.weapon_list[weapon]['filename']
				self.weapon_img = self.weapon_list[weapon]['img']
				self.weapon_damage = self.weapon_list[weapon]['damage']
				self.weapon_delay = self.weapon_list[weapon]['delay']
				if(self.weapon_list[weapon]['speed']>0):
					self.weapon_list[weapon]['speed'] *= -1
				self.weapon_speed = self.weapon_list[weapon]['speed']
				
			msg = f' <<[{i+1}]'
			img_font = self.mfont.render(msg, True, (192,0,192))
			rect_font = img_font.get_rect()

			img = self.weapon_list[weapon]['img']	
			rect = img.get_rect()
			rect_font.x = rect.right+2
			rect_font.centery = rect.centery
					
			temp_surface = pygame.Surface((img.get_size()[0]+img_font.get_size()[0]+2,img.get_size()[1]))
			
			temp_surface.blit(img, (0, 0))
			temp_surface.set_alpha(80)
			temp_surface.blit(img_font, rect_font)
			
			rect.right = self.screen.get_width()-100
			if rect_pre is not None:
				rect.top = rect_pre.bottom+10
			self.screen.blit(temp_surface,rect)
			rect_pre = rect
			
	def draw(self,group_enemy:pygame.sprite.Group):
		if self.is_start:
			self.is_start = False
			self.reset()
		# pygame.draw.rect(self.screen,(255,255,255),rect,1)  
		self.key_pressed()
		
		if self.rect.x < 0:
			self.rect.x = 0
		if self.rect.right > self.screen.get_width():
			self.rect.right = self.screen.get_width()
			
		if self.rect.y < 0:
			self.rect.y = 0
		if self.rect.bottom > self.screen.get_height():
			self.rect.bottom = self.screen.get_height()
			
		items = pygame.sprite.spritecollide(self,self.group_items,True)	
		for item in items:
			self.hp += item.hp
			if item.weapon_img is not None:
				# self.weapon_filename = item.weapon_filename
				# self.weapon_img = item.weapon_img
				# self.weapon_damage = item.weapon_damage
				# self.weapon_delay = item.weapon_delay
				# self.weapon_speed = item.weapon_speed
				
				self.set_weapon_list(item.weapon_filename,item.weapon_img,item.weapon_damage,item.weapon_speed,item.weapon_delay)
			if self.snd_dic['item'] is not None:
				self.snd_dic['item'].play()
			# self.weapon_speed = item.speed*-1
		
		for enemy in group_enemy:			
			# if pygame.sprite.spritecollide(self,enemy.group_weapon,True):
			for w_weapon in enemy.group_weapon:
				if self.rect.colliderect(w_weapon.rect):
					self.hp -= w_weapon.damage
					self.shield_on = True
					w_weapon.kill()

					if self.hp <= 0:
						self.hp = 0		
						self.game_over = True
						if self.snd_dic['game_over'] is not None:
							self.snd_dic['game_over'].play()
					else:
						if self.snd_dic['shock'] is not None:
							self.snd_dic['shock'].play()
				else:
					if pygame.sprite.spritecollide(w_weapon,self.group_weapon,True):
						w_weapon.kill()
						
						if self.snd_dic['hit'] is not None:
							self.snd_dic['hit'].play()
			
			weapons = pygame.sprite.spritecollide(enemy,self.group_weapon,False)			
			for weapon in weapons:
				pygame.sprite.spritecollide(weapon,enemy.group_weapon,True)
				enemy.hp -= weapon.damage
				enemy.shield_on = True
				
				if self.snd_dic['hit'] is not None:
					self.snd_dic['hit'].play()
				if enemy.hp <= 0:
					self.score += enemy.hp_max
										
					if enemy.i_img is not None:
						item = Items(self.screen,
										enemy.i_img,
										enemy.rect.centerx,
										enemy.rect.centery,
										enemy.i_hp,
										enemy.i_weapon_filename,
										enemy.i_weapon_img,
										enemy.i_weapon_damage,
										enemy.i_weapon_delay,
										enemy.i_weapon_speed,
				    						)
						self.group_items.add(item)						
					
					enemy.kill()
					break
				weapon.kill()
			else:
				if self.rect.colliderect(enemy.rect):
					self.hp -= enemy.hp
					self.shield_on = True
					enemy.kill()
					if self.hp <= 0:
						self.hp = 0
						self.game_over = True
						if self.snd_dic['game_over'] is not None:
							self.snd_dic['game_over'].play()
					else:						
						if self.snd_dic['shock'] is not None:
							self.snd_dic['shock'].play()
		self.draw_items()
		self.draw_shield()
		self.group_items.update()
		self.group_weapon.update()
		
		self.group_items.draw(self.screen)
		self.group_weapon.draw(self.screen)
		self.screen.blit(self.image,self.rect)
		
		if self.level in self.score_set_level:
			if self.score >= self.score_set_level[self.level]:
				self.level += 1
				
		if self.level in self.speed_set_level:
			self.speed = self.speed_set_level[self.level]
