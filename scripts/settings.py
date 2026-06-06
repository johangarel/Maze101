
WIDTH = 960
HEIGHT = 740
HEIGHT_SETTINGS = 840

NB_LEVELS = 101
TILE_SIZE = 40

FPS = 240
FPS_PRESETS = [60,120,240]

DEFAULT_MUSIC_VOL = 0.5
DEFAULT_SFX_VOL = 0.5

PLAYER_SPEED = 400
PLAYER_WIDTH = 25
PLAYER_DEFAULT_POS = (WIDTH // 2 - PLAYER_WIDTH // 2, HEIGHT - 50)
PLAYER_HEALTH = 100

ENEMY_SPEED_PATROL = 150
ENEMY_SPEED_CHASE = 400
ENEMY_DETECTION_RADIUS = 200

TP_WIDTH = 50
WINPAD_WIDTH = 50
VISION_RADIUS = 150

TORCH_EFFECT = 200
TORCH_TIME = 5.0

HEAL_EFFECT = 50

SPEED_EFFECT = 200
SPEED_TIME = 5.0

WALL_THICKNESS = 10

FADE_SPEED = {
    "slow":10,
    "normal":25,
    "fast":50
}

GAME_NAME = "MAZE 101"
GAME_VERSION = "v0.5 WIP"
START_TEXT = "START"
PLAY_TEXT = "PLAY"
VICTORY_TEXT = "You win !"
LOADING_TEXT = "Loading..."
RECORD_TEXT = "New record !"
SETTINGS_TITLE = "Settings"
SAVE_TEXT = "Save changes"
RESET_TEXT = "Reset"

TUTORIAL_FR_TEXT = [
    "Se déplacer : ZQSD",
    "Couper/Réactiver la musique : E",
    "Revenir au menu principal : Echap",
    "Changer le niveau dans le menu : Q/D",
    "Réinitialiser le labyrinthe : R"
]

TUTORIAL_EN_TEXT = [
    "Move : ZQSD",
    "Mute/Unmute the music : E",
    "Go back to the main menu : Escape",
    "Change level in menu : Q/D",
    "Reset maze : R"
]

KEY_COLORS = {
    'a': (255, 50, 50),   
    'b': (50, 255, 50),   
    'c': (50, 50, 255),   
    'd': (255, 255, 50),  
    'e': (255, 50, 255)
}

DEFAULT_KEY_COLOR = (200, 200, 200)

# Objects that walls shouldn't connect with
BANNED_BUILDING_CHARACTERS = ["P","L","S","E","V","H"]

KEY_BINDINGS_DEFAULT = {
    "up":     "K_z",
    "down":   "K_s",
    "left":   "K_q",
    "right":  "K_d",
    "music":  "K_e",
    "reset":  "K_r",
    "menu":   "K_ESCAPE",
}

INVICIBILITY_TIME = 1.0
SHADOW_DELAY = 3.0