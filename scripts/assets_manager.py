import pygame
from .utils import get_path

class AssetsManager:
    """
    Manager class for loading and storing all game assets (images, sounds, fonts).
    
    This class handles the initialization of pygame subsystems and provides
    a dictionary-like interface to access loaded assets.
    """

    def __init__(self):
        
        # Initialize pygame subsystems
        pygame.mixer.init()
        pygame.font.init()
        
        # Dictionary to store all assets
        self._assets = {}
        
        # Load all asset categories
        self._load_images()
        self._load_sounds()
        self._load_fonts()

    def _load_images(self):
        """
        Load all image assets from the assets/images directory.
        Stores loaded images in the internal assets dictionary.
        """
        images = {
            "logo": "LOGO PROJECT 1.png",
            "winpad": "_crown_new.png",
            "tp1": "_tp_new.png",
            "tp2": "_tp2_new.png",
            "tp3": "_tp3_new.png",
            "music_on": "MUSIC ON.png",
            "music_off": "MUSIC OFF.png",
            "home": "THE HOUSE.png",
            "right_arrow": "_arrow_right.png",
            "right_double_arrow": "_arrow_righter.png",
            "left_arrow": "_arrow_left.png",
            "left_double_arrow": "_arrow_lefter.png",
            "tutorial_fr": "book_fr.png",
            "tutorial_en": "book_en.png",
            "trap": "trap.png",
            "key": "key.png",
            "star": "STAR.png",
            "completed": "YES.png",
            "torch": "Light.png",
            "settings":"settings.png",
            "player":"player.png",
            "enemy":"enemy.png",
            "shadow":"shadow.png",
            "heal":"HEALTH.png",
            "speed":"SPEED.png",
            "_dynamic_wall": "_dynamic_wall.png",
            "shield":"SHIELD.png"
        }
        
        for key, filename in images.items():
            try:
                path = get_path("assets", "images", filename)
                self._assets[key] = pygame.image.load(path)
                if key == "player":
                    # Player additional assets
                    base = self._assets[key]
                    self._assets["player_right"] = base
                    self._assets["player_left"]  = pygame.transform.flip(base, True, False)
                    self._assets["player_up"]    = pygame.transform.rotate(base, 90)
                    self._assets["player_down"]  = pygame.transform.rotate(base, -90)
                elif key == "enemy":
                    # Enemy additional assets
                    base = self._assets[key]
                    self._assets["enemy_right"] = base
                    self._assets["enemy_left"]  = pygame.transform.flip(base, True, False)
                    self._assets["enemy_up"]    = pygame.transform.rotate(base, 90)
                    self._assets["enemy_down"]  = pygame.transform.rotate(base, -90)
                elif key == "shadow":
                    # Shadow additional assets
                    base = self._assets[key]
                    self._assets["shadow_right"] = base
                    self._assets["shadow_left"]  = pygame.transform.flip(base, True, False)
                    self._assets["shadow_up"]    = pygame.transform.rotate(base, 90)
                    self._assets["shadow_down"]  = pygame.transform.rotate(base, -90)
            except pygame.error as e:
                print(f"Warning: Could not load image '{key}' from {filename}: {e}")
        


    def _load_sounds(self):
        """
        Load all sound assets (music and sound effects) from assets/sounds directory.
        Stores loaded sounds in the internal assets dictionary.
        """
        # Load background music tracks
        music_files = {
            "menu_music": "sounds/_cool_menu_music.mp3",
            "music_victory": "sounds/_victory.mp3",
            "music_level1": "sounds/_level1.mp3",
            "music_level2": "sounds/_level2.mp3",
            "music_level3": "sounds/_level3.mp3",
            "music_level4": "sounds/_level4.mp3",
            "music_level42": "sounds/_level42.mp3",
        }
        
        # Load sound effects
        sfx_files = {
            "sfx_death": "sounds/sfx/sfx_reset.ogg",
            "sfx_teleport": "sounds/sfx/sfx_teleport.ogg",
            "sfx_win": "sounds/sfx/sfx_win.ogg",
            "sfx_unlock": "sounds/sfx/sfx_unlock.ogg",
            "sfx_play": "sounds/sfx/sfx_play.ogg",
            "sfx_key": "sounds/sfx/sfx_key.ogg",
            "sfx_walk1": "sounds/sfx/sfx_walk1.ogg",
            "sfx_walk2": "sounds/sfx/sfx_walk2.ogg",
            "sfx_walk3": "sounds/sfx/sfx_walk3.ogg",
            "sfx_walk4": "sounds/sfx/sfx_walk4.ogg",
            "sfx_light": "sounds/sfx/sfx_light.ogg",
        }
        
        # Load all sound files
        all_sounds = {**music_files, **sfx_files}
        for key, relative_path in all_sounds.items():
            try:
                path = get_path("assets", relative_path)
                self._assets[key] = pygame.mixer.Sound(path)
            except pygame.error as e:
                print(f"Warning: Could not load sound '{key}' from {relative_path}: {e}")

    def _load_fonts(self):
        """
        Create and store font objects for different text sizes.
        Uses default pygame font with various sizes for UI elements.
        """
        self._assets["font_main"] = pygame.font.Font(None, 144)
        self._assets["font_medium"] = pygame.font.Font(None, 64)
        self._assets["font_small"] = pygame.font.Font(None, 40)
    
    def _rotated(surface, angle, size):
        rotated = pygame.transform.rotate(surface, angle)
        return pygame.transform.smoothscale(rotated, (size, size))

def load_assets():
    return AssetsManager()