
import os
try:
    import pygame
except:
    os.system('pip install pygame')
    import pygame

try:
    import win32api
except:
    os.system('pip install pywin32')
    import win32api
    
import win32con
import win32gui
import ctypes
import math

try:
    from pystray import Icon, MenuItem, Menu
except:
    os.system('pip install pystray')
    from pystray import Icon, MenuItem, Menu

try:
    from PIL import Image, ImageDraw
except:
    os.system('pip install Pillow')
    from PIL import Image, ImageDraw    
    
import threading


from pygame.event import Event
# RECT 구조체 정의
class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long)]
    # (_fields_)


class MousePointer:
    TRANSPARENT_COLOR = (255, 0, 255) #255, 0, 128
    
    mouse_click = {'left' : False, 'right' : False, 'middle' : False}
    face_expressions = ["smile", "wink", "neutral", "sad"]
    event_func_p = None
    is_run = True
    
    def __init__(self, filename:str=None, screen_width:int=None, screen_height:int=None,size:int=50):
        
        pygame.init()
        if screen_width is not None and screen_height is not None:
            self.screen = pygame.display.set_mode((screen_width, screen_height), pygame.SRCALPHA | pygame.NOFRAME)
        else:
            self.screen = pygame.display.set_mode(self.get_window_size(), pygame.SRCALPHA | pygame.NOFRAME)

        # 윈도우 핸들 가져오기
        self.hwnd = pygame.display.get_wm_info()['window']
        self.set_background_Alpha(self.hwnd)
        self.set_always_on_top(self.hwnd)
        self.hide_window(self.hwnd)
        # win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)

        
        self.cursor_size = size
        if filename is None:
            self.cursor_image_src = None
            self.cursor_image = self.draw_face(self.cursor_size, expression="smile")
        else:
            self.cursor_image_src = pygame.image.load(filename).convert_alpha()
            self.cursor_image = pygame.transform.scale(self.cursor_image_src, (size, size))
        
        # self.cursor_image.set_alpha(90)
        self.cursor_rect = self.cursor_image.get_rect()

        self.clock = pygame.time.Clock()
        
    def draw_face(self,size, expression="smile"):
        WHITE = (255, 255, 255)
        SKIN = (255, 224, 189)
        BLACK = (0, 0, 0)
        RED = (255, 0, 0)
        PINK = (255, 150, 150)
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        radius = int(size * 0.4)

        surface.fill((0, 0, 0, 0))  # 투명 배경

        # 얼굴
        pygame.draw.circle(surface, SKIN, (center, center), radius)

        # 눈
        eye_radius = int(size * 0.05)
        eye_y = int(center - radius * 0.4)
        eye_dx = int(radius * 0.5)
        left_eye_pos = (center - eye_dx, eye_y)
        right_eye_pos = (center + eye_dx, eye_y)

        if expression == "wink":
            pygame.draw.line(surface, BLACK,
                            (right_eye_pos[0] - eye_radius, right_eye_pos[1]),
                            (right_eye_pos[0] + eye_radius, right_eye_pos[1]), 3)
        else:
            pygame.draw.circle(surface, BLACK, right_eye_pos, eye_radius)

        pygame.draw.circle(surface, BLACK, left_eye_pos, eye_radius)

        # 입
        mouth_rect = pygame.Rect(center - radius * 0.5, center + 10, radius, radius * 0.5)

        if expression == "smile":
            pygame.draw.arc(surface, RED, mouth_rect, math.radians(0), math.radians(180), 3)
        elif expression == "sad":
            pygame.draw.arc(surface, RED, mouth_rect.move(0, 20), math.radians(180), math.radians(360), 3)
        elif expression == "neutral":
            pygame.draw.line(surface, RED,
                            (center - radius * 0.3, center + 40),
                            (center + radius * 0.3, center + 40), 3)

        # 볼터치
        cheek_radius = int(size * 0.04)
        cheek_y = int(center)
        pygame.draw.circle(surface, PINK, (center - int(radius * 0.75), cheek_y), cheek_radius)
        pygame.draw.circle(surface, PINK, (center + int(radius * 0.75), cheek_y), cheek_radius)

        return surface
    
    def set_mouse_image(self, event, key,def_expression="smile", change_expression='wink'):       
        
        size = 0
        expression = None 
        if ctypes.windll.user32.GetAsyncKeyState(event) & 0x8000:
            if self.mouse_click[key]==False:
                self.mouse_click[key] = True
                if self.cursor_image_src is None:
                    expression=change_expression
                else:
                    size = self.cursor_size/2
        else:
            if self.mouse_click[key]==True:
                self.mouse_click[key] = False
                
                if self.cursor_image_src is None:
                    expression=def_expression
                else:
                    size = self.cursor_size
        return expression, size
                    

    def get_mouse_click(self):
        VK_LBUTTON = 0x01  # 왼쪽 버튼
        VK_RBUTTON = 0x02  # 오른쪽 버튼
        VK_MBUTTON = 0x04  # 가운데 버튼
        size = 0
        expression = None
        
        expression, size = self.set_mouse_image(VK_LBUTTON, 'left', "smile", "wink")
        if expression is None and size == 0:
            expression, size = self.set_mouse_image(VK_RBUTTON, 'right', "smile", "neutral")
                    
        if expression is not None:
            self.cursor_image = self.draw_face(50, expression)
        elif size != 0:
            self.cursor_image = pygame.transform.scale(self.cursor_image_src, (size, size))
            self.cursor_rect.width = size
            self.cursor_rect.height = size
        
    def RGB(self,r, g, b):
        return r | (g << 8) | (b << 16)
    # 현재 실행 중인 프로세스의 핸들 가져오기
    
    def hide_window(self,hwnd):
        # 창 스타일 변경: 작업표시줄에서 숨기기
        GWL_EXSTYLE = -20
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_APPWINDOW = 0x00040000

        # 기존 스타일 가져오기
        ex_style = win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)

        # APPWINDOW 제거하고 TOOLWINDOW 추가
        ex_style = ex_style & ~WS_EX_APPWINDOW
        ex_style = ex_style | WS_EX_TOOLWINDOW

        # 스타일 적용
        win32gui.SetWindowLong(hwnd, GWL_EXSTYLE, ex_style)

        # 창 위치 재설정 (스타일 변경 후 필요)
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        
# 좌표 얻기 함수
    def get_window_position(self,hwnd):
        rect = RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        x = rect.left
        y = rect.top
        return x, y

    def get_window_size(self,):
        u32 = ctypes.windll.user32
        resolution = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
        return resolution
    
    def set_background_Alpha(self, hwnd):
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(
                       hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)

        # win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(255,0,128), 0, win32con.LWA_COLORKEY)
        win32gui.SetLayeredWindowAttributes(hwnd, self.RGB(*self.TRANSPARENT_COLOR), 0, win32con.LWA_COLORKEY)

    def set_always_on_top(self,hwnd):
        # 상수 정의
        HWND_TOPMOST = -1
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_SHOWWINDOW = 0x0040

        # 항상 위로 설정
        ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                                        SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)

    def get_cursor_position(self,hwnd,cursor_rect):
        sx,sy = self.get_window_position(hwnd)
        # 마우스 위치 얻기
        mouse_x, mouse_y = win32api.GetCursorPos()
        
        cursor_rect.centerx = mouse_x
        cursor_rect.y = mouse_y+10

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
                
        if self.is_run==False:
            return False
        return True
    
    # 아이콘 이미지를 생성하는 함수
    def create_image(self):
        # 64x64 사이즈의 이미지 생성
        image = Image.new('RGB', (64, 64), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill=(0, 0, 0))
        return image

    # 종료 함수
    def on_quit(self,icon, item):
        self.is_run = False
        icon.stop()

    # 트레이 아이콘을 실행하는 함수
    def setup_tray_icon(self):
        icon = Icon("Test Tray", self.create_image(), menu=Menu(
            MenuItem("종료", self.on_quit)
        ))
        icon.run()
     
    def run(self):
        threading.Thread(target=self.setup_tray_icon, daemon=True).start()
        while self.check_quit():
            # 완전 투명하게 배경 지우기
            self.screen.fill(self.TRANSPARENT_COLOR)
            self.get_cursor_position(self.hwnd, self.cursor_rect)
            self.get_mouse_click()
            
            self.screen.blit(self.cursor_image, self.cursor_rect)
            pygame.display.update()
            self.clock.tick(60)

if __name__ == "__main__":
    mouse_pointer = MousePointer()
    mouse_pointer.run()
        
