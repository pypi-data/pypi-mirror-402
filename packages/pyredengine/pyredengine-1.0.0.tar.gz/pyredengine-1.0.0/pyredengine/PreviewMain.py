# Main project file
import pygame, sys, os, inspect, math
from typing import TypeVar
from forbiddenfruit import curse
import pygame.gfxdraw
        
    
class EngineStats:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EngineStats, cls).__new__(cls)
            cls._instance._engine_current_blit_count = 0
            cls._instance._engine_previous_blit_count = 0
            cls._instance._engine_blits_per_second = 0
            
            cls._instance._engine_current_draw_count = 0
            cls._instance._engine_previous_draw_count = 0
            cls._instance._engine_draws_per_second = 0
            
            
        return cls._instance
    
    def get_bps(self):
        # Access the singleton instance directly
        return self._engine_blits_per_second

    def get_total_blits(self):
        return self._engine_current_blit_count
    
    def get_dps(self):
        # Access the singleton instance directly
        return self._engine_draw_per_second
    
    
    def get_total_draws(self):
        return self._engine_current_draw_count

    def get_is_ce(self):
        try:
            if pygame.IS_CE:
                return True
        except Exception as e:
            return False

    def get_is_prerel(self):
        return "dev" in pygame.version.ver

def monkey_patch_function_b(target_class, method_name):
    """Monkey patch a method to increment the blit count."""
    
    # Get the original method
    original_method = getattr(target_class, method_name)

    # Define the new method that wraps the original
    def patched_method(*args, **kwargs):
        EngineStats()._engine_current_blit_count += 1  # Increment count
        return original_method(*args, **kwargs)  # Call the original method

    # Use curse to replace the original method
    curse(target_class, method_name, patched_method)
    
def monkey_patch_function_d(method):
    """Monkey patch a method to increment the blit count."""
    
    # Get the original method
    original_method = method

    # Define the new method that wraps the original
    def patched_method(*args, **kwargs):
        EngineStats()._engine_current_draw_count += 1  # Increment count
        return original_method(*args, **kwargs)  # Call the original method

    # Use curse to replace the original method
    return patched_method
    
def monkey_patch_function_d_array(method):
    """Monkey patch a method to increment the blit count."""
    
    # Get the original method
    original_method = method

    # Define the new method that wraps the original
    def patched_method(*args, **kwargs):
        count = 0
        if args:
            for i in args:
                if isinstance(i, (list, tuple)):
                    count += len(i)  # Count the number of blits
                    
        EngineStats()._engine_current_blit_count += count
        return original_method(*args, **kwargs)  # Call the original method

    # Use curse to replace the original method
    return patched_method
       
def _monkey_patch():
    # Store the original blit method
    original_blit = pygame.Surface.blit
    original_blits = pygame.Surface.blits

    # Custom blit function
    def custom_blit(*args, **kwargs):
        EngineStats()._engine_current_blit_count += 1
        return original_blit(*args, **kwargs)
    
    def custom_blits(*args, **kwargs):
        count = 0
        if args:
            for i in args:
                if isinstance(i, (list, tuple)):
                    count += len(i)  # Count the number of blits

            
        # Check if kwargs contain blit_sequence
        if 'blit_sequence' in kwargs:
            blit_sequence = kwargs['blit_sequence']
            if isinstance(blit_sequence, (list, tuple)):
                count += len(blit_sequence)  # Count the number of blits

        EngineStats()._engine_current_blit_count += count
        return original_blits(*args, **kwargs)

    def custom_fblits(*args, **kwargs):
        count = 0
        # Check if kwargs contain blit_sequence
        if 'blit_sequence' in kwargs:
            blit_sequence = kwargs['blit_sequence']
            if isinstance(blit_sequence, (list, tuple)):
                count += len(blit_sequence)  # Count the number of blits
                
        elif args:
            for i in args:
                if isinstance(i, (list, tuple)):
                    count += len(i)  # Count the number of blits

            


        EngineStats()._engine_current_blit_count += count
        return original_blits(*args, **kwargs)
    
    def custom_groupDraw(*args, **kwargs):
        count = 0
        if "self" in args:
            count = len(args[0].sprites())
            
        EngineStats()._engine_current_blit_count += count
        return original_blits(*args, **kwargs)
        

    # Monkey patching blit
    curse(pygame.Surface, "blit", custom_blit)
    curse(pygame.Surface, "blits", custom_blits)
    curse(pygame.sprite.Group, "draw", custom_groupDraw)
    if EngineStats().get_is_ce(): curse(pygame.Surface, "fblits", custom_fblits)
    
    

    pygame.draw.rect = monkey_patch_function_d(pygame.draw.rect)
    pygame.draw.polygon = monkey_patch_function_d(pygame.draw.polygon)
    pygame.draw.circle = monkey_patch_function_d(pygame.draw.circle)
    pygame.draw.aacircle = monkey_patch_function_d(pygame.draw.aacircle)
    pygame.draw.ellipse = monkey_patch_function_d(pygame.draw.ellipse)
    pygame.draw.arc = monkey_patch_function_d(pygame.draw.arc)
    pygame.draw.line = monkey_patch_function_d(pygame.draw.line)
    pygame.draw.lines = monkey_patch_function_d_array(pygame.draw.lines)
    pygame.draw.aaline = monkey_patch_function_d(pygame.draw.aaline)
    pygame.draw.aalines = monkey_patch_function_d_array(pygame.draw.line)
    
    pygame.gfxdraw.pixel = monkey_patch_function_d(pygame.gfxdraw.pixel)
    pygame.gfxdraw.hline = monkey_patch_function_d(pygame.gfxdraw.hline)
    pygame.gfxdraw.line = monkey_patch_function_d(pygame.gfxdraw.line)
    pygame.gfxdraw.rectangle = monkey_patch_function_d(pygame.gfxdraw.rectangle)
    pygame.gfxdraw.box = monkey_patch_function_d(pygame.gfxdraw.box)
    pygame.gfxdraw.circle = monkey_patch_function_d(pygame.gfxdraw.circle)
    pygame.gfxdraw.aacircle = monkey_patch_function_d(pygame.gfxdraw.aacircle)
    pygame.gfxdraw.filled_circle = monkey_patch_function_d(pygame.gfxdraw.filled_circle)
    pygame.gfxdraw.ellipse = monkey_patch_function_d(pygame.gfxdraw.ellipse)
    pygame.gfxdraw.filled_ellipse = monkey_patch_function_d(pygame.gfxdraw.filled_ellipse)
    pygame.gfxdraw.aaellipse = monkey_patch_function_d(pygame.gfxdraw.aaellipse)
    pygame.gfxdraw.arc = monkey_patch_function_d(pygame.gfxdraw.arc)
    pygame.gfxdraw.pie = monkey_patch_function_d(pygame.gfxdraw.pie)
    pygame.gfxdraw.trigon = monkey_patch_function_d(pygame.gfxdraw.trigon)
    pygame.gfxdraw.aatrigon = monkey_patch_function_d(pygame.gfxdraw.aatrigon)
    pygame.gfxdraw.filled_trigon = monkey_patch_function_d(pygame.gfxdraw.filled_trigon)
    pygame.gfxdraw.polygon = monkey_patch_function_d(pygame.gfxdraw.polygon)
    pygame.gfxdraw.aapolygon = monkey_patch_function_d(pygame.gfxdraw.aapolygon)
    pygame.gfxdraw.filled_polygon = monkey_patch_function_d(pygame.gfxdraw.filled_polygon)
    pygame.gfxdraw.textured_polygon = monkey_patch_function_d(pygame.gfxdraw.textured_polygon)
    pygame.gfxdraw.bezier = monkey_patch_function_d(pygame.gfxdraw.bezier)
    
_monkey_patch()




class MainGame:
    def __init__(self, fullscreen, resolution = [1280, 720]) -> None:
        pygame.init()

        self._fullscreen = fullscreen
        self._init_display(resolution=resolution)
        self.clock = pygame.time.Clock()
        self.run = True
        
        self.mouse_pos = (0,0) 
        self._engine_mode = True
        self._ms = 0
        



        
        
    def _init_display(self, resolution = [1280, 720], caption = "Pygame Window"): # Don't touch 
        # sourcery skip: default-mutable-arg
        """Initialises the display to be rendered within the viewport window of the engine"""
        self._hwnd = None
        if len(sys.argv) > 1:
            self._hwnd = int(sys.argv[1])
            os.environ['SDL_WINDOWID'] = str(self._hwnd)
        
        self.display_width = resolution[0]
        self.display_height = resolution[1]
        

        if self._fullscreen:
            print("IS FULLSCREEN")
            
            os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (250, 100)
            self.display = pygame.display.set_mode((self.display_width, self.display_height))
        else:
            print("IS EMBEDDED")
            os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (-100000, -100000)
            self.display = pygame.display.set_mode((self.display_width, self.display_height), pygame.NOFRAME)

        pygame.display.set_caption(caption)
        
    def _send_event(self, type, key = None, mouse = None):
        """Manages event handling between viewport window and the game
           Mouse = x, y, button_down(type)
        
        """
        if type == 1: # Keyboard press
            event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.key.key_code(key)})
            pygame.event.post(event)
            
        elif type == 2: # Mouse Movement
            mouse_x, mouse_y, mouse_down = mouse
            self.mouse_rel = mouse_x - self.mouse_pos[0], mouse_y - self.mouse_pos[1]
                                  
            event = pygame.event.Event(pygame.MOUSEMOTION, {'pos': (mouse_x, mouse_y), 'rel': (self.mouse_rel[0], self.mouse_rel[1]) , 'buttons': pygame.mouse.get_pressed()})
            pygame.event.post(event)
            
            self.mouse_pos = mouse_x, mouse_y   
            
        elif type == 3: # Mouse Press
            mouse_x, mouse_y, mouse_down = mouse
            self.mouse_rel = mouse_x - self.mouse_pos[0], mouse_y - self.mouse_pos[1]
                   
            event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": mouse_down, "pos": (mouse_x, mouse_y)})
            pygame.event.post(event)
            
            self.mouse_pos = mouse_x, mouse_y   

        elif type == 4: # Mouse Release
            mouse_x, mouse_y, mouse_up = mouse
            self.mouse_rel = mouse_x - self.mouse_pos[0], mouse_y - self.mouse_pos[1]
                       
            event = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": mouse_up, "pos": (mouse_x, mouse_y)})
            pygame.event.post(event)
            
            self.mouse_pos = mouse_x, mouse_y   



    def handle_events(self):
        """Handles custom user events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close_game()

            
    def update(self):
        """Put all your custom logic here"""
        pass
    
    def draw(self):
        """Custom drawing logic here"""
        pygame.display.flip()
    
    def on_reload(self):
        pass
        
        
    def on_save(self):
        pass
    
    def run_game(self):
        """Handles the running of the game"""
        self._ms = 0
        while self.run: # Don't touch
            EngineStats()._engine_previous_blit_count = EngineStats()._engine_current_blit_count
            EngineStats()._engine_previous_draw_count = EngineStats()._engine_current_draw_count
            
            self._ms = self.clock.tick()
            self.handle_events()
            self.update()
            self.draw()
            
            EngineStats()._engine_blits_per_second = EngineStats()._engine_previous_blit_count - EngineStats()._engine_current_blit_count 
            EngineStats()._engine_draws_per_second = EngineStats()._engine_previous_draw_count - EngineStats()._engine_current_draw_count 
                        
            yield self.display

        pygame.quit()
        #sys.exit()
        
    def  _obtain_user_vars(self):
        all_vars = globals()

        # Get only user-defined variables, excluding built-ins and imports
        current_frame = inspect.currentframe()
        return {
            k: v
            for k, v in all_vars.items()
            if not k.startswith("__")  # Exclude built-ins
            and k
            in current_frame.f_globals  # Check if variable is in the current script's scope
            and not inspect.ismodule(v)
        }
    
    def close_game(self):
        self.run = False
        pygame.quit()
    
    def get_dt(self):
        return self._ms
    
    def get_clock(self):
        return self.clock
    
    def get_tick(self):
        return pygame.time.get_ticks()

    def get_bps(self):
        return math.floor(EngineStats()._engine_blits_per_second)
    
    def get_total_blits(self):
        return math.floor(EngineStats()._engine_current_blit_count)
    
    def get_draw_calls(self):
        return math.floor(EngineStats()._engine_current_draw_count)
    
    def get_dps(self):
        return math.floor(EngineStats()._engine_draws_per_second)
    
    
