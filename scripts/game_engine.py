import os
import pygame
from pygame.locals import *

from .entities import (Player, Door, Key, Trap, Winpad, Portal, ButtonUI, 
                       Light, SubMapPortal, TextUI, Shadow, Heal, Speed, 
                       DynamicWall, Shield)
from .utils import invert_color
from .settings import (
    WIDTH, HEIGHT, NB_LEVELS, TILE_SIZE, FPS,
    PLAYER_SPEED, PLAYER_WIDTH, PLAYER_DEFAULT_POS,
    FADE_SPEED,
    TORCH_EFFECT, TORCH_TIME,
    GAME_NAME, GAME_VERSION, START_TEXT, PLAY_TEXT, RECORD_TEXT,
    VICTORY_TEXT, LOADING_TEXT, TUTORIAL_FR_TEXT, TUTORIAL_EN_TEXT,
    KEY_COLORS, DEFAULT_KEY_COLOR, SETTINGS_TITLE, FPS_PRESETS,
    HEIGHT_SETTINGS, SAVE_TEXT, RESET_TEXT,
    DEFAULT_MUSIC_VOL, DEFAULT_SFX_VOL, HEAL_EFFECT, PLAYER_HEALTH,
    SPEED_TIME, SPEED_EFFECT, SHIELD_TIME, SHADOW_DELAY
)
from .assets_manager import AssetsManager
from .audio_manager import AudioManager
from .level_manager import LevelManager
from .progress_manager import ProgressManager
from .game_state import GameState


class Game:
    """
    Main coordinator.

    Responsibilities here:
      - Main loop (run)
      - Window construction and UI widgets
      - Event dispatch to managers
      - Final rendering (relies on data exposed by managers)
    """

    def __init__(self):
        # --- Pygame ---
        pygame.init()

        # --- Dimensions ---
        self.width = WIDTH
        self.height = HEIGHT
        self.default_window_size = (WIDTH, HEIGHT)
        self.tile_size = TILE_SIZE
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(GAME_NAME)
        self.center_x = self.screen.get_rect().centerx
        self.center_y = self.screen.get_rect().centery

        # --- Loading screen ---
        self.loading_text = TextUI(self.center_x, self.center_y, pygame.font.Font(None,144), LOADING_TEXT, (255, 255, 255))
        self.screen.blit(self.loading_text.txt, self.loading_text.pos)
        pygame.display.flip()

        # --- Assets ---
        self.assets = AssetsManager()._assets
        pygame.display.set_icon(self.assets["logo"])

        # --- Managers ---
        self.progress  = ProgressManager(NB_LEVELS)
        self.audio     = AudioManager(self.assets, {"music": self.progress.music_on, "music_vol": self.progress.music_vol, "sfx_vol": self.progress.sfx_vol})
        self.levels    = LevelManager(
            player=Player(PLAYER_DEFAULT_POS, PLAYER_SPEED, PLAYER_WIDTH, self.assets["player"])
        )
        self.player: Player = self.levels._player   # convenient shortcut
        
        # --- Shadow system ---
        self.shadows = []
        self.levels.shadows = self.shadows
        self.shadow_start_time = 0.0

        # --- Game state ---
        self.state      = GameState.MAIN_MENU
        self.maze       = 0      # active level (1-based, 0 = menu)
        self.level_menu = 0
        self.current_map_index = 0  # indice de la sous-carte active
        self.active     = True
        self.binding_action = None

        # --- Timing ---
        self.clock      = pygame.time.Clock()
        self.fps        = FPS
        self.dt         = 0.0
        self.timer      = 0
        self.seconds    = 0.0
        self.walk_timer = 0.0

        # --- UI Colors ---
        self.font_color        = (0, 0, 0)
        self.second_font_color = (255, 255, 255)
        self.fade_speed        = FADE_SPEED
        self.level_colors      = {
            level_id: cfg.get("color", (255, 255, 255))
            for level_id, cfg in self.levels.level_configs.items()
        }
        self.level_names       = {
            level_id: cfg.get("name", f"Level {level_id}")
            for level_id, cfg in self.levels.level_configs.items()
        }
        self.level_stars       = {
            level_id: cfg.get("reward", 0)
            for level_id, cfg in self.levels.level_configs.items()
        }
        self.nb_levels         = NB_LEVELS

        # --- Text & buttons ---
        self._build_ui()

        # --- End of loading ---
        self.fade_to_black(self.width, self.height, self.fade_speed["normal"])

    # ==================================================================
    # Main loop
    # ==================================================================

    def run(self):
        while self.active:
            self.handle_events()
            self.update()
            self.render()
        pygame.quit()

    # ==================================================================
    # Events
    # ==================================================================

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.active = False

            elif event.type == KEYDOWN:
                if self.binding_action and event.key not in self.progress.keys.values():
                    self.progress.keys[self.binding_action] = event.key
                    self.binding_action = None # On arrête l'écoute
                    return
                
                # Music [E]
                if event.key == self.progress.keys["music"]:
                    music_on = self.audio.toggle()
                    self.progress.save_music_pref(music_on)

                # Menu return [Escape]
                elif event.key == self.progress.keys["menu"] and self.state != GameState.MAIN_MENU:
                    self._go_to_menu()

                # Level menu navigation
                elif self.state == GameState.LEVEL_MENU:
                    if event.key == self.progress.keys["right"]:
                        self._press_right()
                    elif event.key == self.progress.keys["left"]:
                        self._press_left()

                # Reset level [R]
                elif self.state == GameState.MAZE and event.key == self.progress.keys["reset"]:
                    self._respawn()

            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                self._handle_click(mx, my)

    def _handle_click(self, mx, my):
        if self.state == GameState.LEVEL_MENU:
            btn = self.button_levels[self.level_menu - 1]
            # Only allow starting level if it has a valid configuration
            if btn.is_pressed(mx, my) and not self._is_level_empty(self.level_menu):
                self._start_level(self.level_menu)

            if self.button_left_arrow.is_pressed(mx, my):
                self._press_left()
            if self.button_right_arrow.is_pressed(mx, my):
                self._press_right()
            if self.button_left_arrow2.is_pressed(mx, my):
                self._jump_left()
            if self.button_right_arrow2.is_pressed(mx, my):
                self._jump_right()

        elif self.state in (GameState.FRENCH_TUTORIAL, GameState.ENGLISH_TUTORIAL):
            if self.button_home.is_pressed(mx, my):
                self.state = GameState.MAIN_MENU
                self.fade_to_black(self.width, self.height, self.fade_speed["normal"])

        elif self.state == GameState.VICTORY_MENU:
            if self.button_home.is_pressed(mx, my):
                self._go_to_menu()

        elif self.state == GameState.MAIN_MENU:
            if self.button_start.is_pressed(mx, my):
                self.state = GameState.LEVEL_MENU
                self.level_menu = 1
                self.fade_to_black(self.width, self.height, self.fade_speed["normal"])
            if self.button_book_fr.is_pressed(mx, my):
                self.state = GameState.FRENCH_TUTORIAL
                self.fade_to_black(self.width, self.height, self.fade_speed["normal"])
            if self.button_book_en.is_pressed(mx, my):
                self.state = GameState.ENGLISH_TUTORIAL
                self.fade_to_black(self.width, self.height, self.fade_speed["normal"])
            if self.button_settings.is_pressed(mx, my):
                self.state = GameState.SETTINGS_MENU
                self.fade_to_black(self.width, self.height, self.fade_speed["normal"])
                self.height = HEIGHT_SETTINGS
                os.environ["SDL_VIDEO_WINDOW_POS"] = "center"
                self.screen = pygame.display.set_mode((self.width, self.height))
            
        elif self.state == GameState.SETTINGS_MENU:
            if self.button_home.is_pressed(mx, my): # Home
                self._go_to_menu()

            # FPS
            if self.button_fps_arrow_left.is_pressed(mx, my):
                i = FPS_PRESETS.index(self.fps)
                self.fps = FPS_PRESETS[len(FPS_PRESETS)-1] if i == 0 else FPS_PRESETS[i-1]
                self.fps_value = TextUI(
                    self.button_fps_arrow_right.centerx - 125, self.button_fps_arrow_left.centery, self.assets["font_medium"], str(self.fps), (255, 255, 255)
                )
            if self.button_fps_arrow_right.is_pressed(mx, my):
                i = FPS_PRESETS.index(self.fps)
                self.fps = FPS_PRESETS[0] if i == len(FPS_PRESETS)-1 else FPS_PRESETS[i+1]
                self.fps_value = TextUI(
                    self.button_fps_arrow_right.centerx - 125, self.button_fps_arrow_left.centery, self.assets["font_medium"], str(self.fps), (255, 255, 255)
                )
            
            # Music
            if self.button_vol_music_left.is_pressed(mx, my) and self.audio.music_vol > 0:
                self.audio.music_vol = round(self.audio.music_vol - 0.1, 1)
                self.audio.update_volume()
                self.music_vol = TextUI(
                    self.button_vol_music_right.centerx - 125, self.button_vol_music_left.centery, self.assets["font_medium"], str(int(100*self.audio.music_vol))+" %", (255, 255, 255)
                )
            if self.button_vol_music_right.is_pressed(mx, my) and self.audio.music_vol < 1:
                self.audio.music_vol = round(self.audio.music_vol + 0.1, 1)
                self.audio.update_volume()
                self.music_vol = TextUI(
                    self.button_vol_music_right.centerx - 125, self.button_vol_music_left.centery, self.assets["font_medium"], str(int(100*self.audio.music_vol))+" %", (255, 255, 255)
                )
            
            # SFX
            if self.button_vol_sfx_left.is_pressed(mx, my) and self.audio.sfx_vol > 0:
                self.audio.sfx_vol = round(self.audio.sfx_vol - 0.1, 1)
                self.sfx_vol = TextUI(
                    self.button_vol_sfx_right.centerx - 125, self.button_vol_sfx_left.centery, self.assets["font_medium"], str(int(100*self.audio.sfx_vol))+" %", (255, 255, 255)
                )
            if self.button_vol_sfx_right.is_pressed(mx, my) and self.audio.sfx_vol < 1:
                self.audio.sfx_vol = round(self.audio.sfx_vol + 0.1, 1)
                self.sfx_vol = TextUI(
                    self.button_vol_sfx_right.centerx - 125, self.button_vol_sfx_left.centery, self.assets["font_medium"], str(int(100*self.audio.sfx_vol))+" %", (255, 255, 255)
                )
            
            # Key bindings
            if self.button_key_bindings["up"].is_pressed(mx, my):
                self.binding_action = "up"
            if self.button_key_bindings["down"].is_pressed(mx, my):
                self.binding_action = "down"
            if self.button_key_bindings["left"].is_pressed(mx, my):
                self.binding_action = "left"
            if self.button_key_bindings["right"].is_pressed(mx, my):
                self.binding_action = "right"
            if self.button_key_bindings["reset"].is_pressed(mx, my):
                self.binding_action = "reset"
            if self.button_key_bindings["menu"].is_pressed(mx, my):
                self.binding_action = "menu"
            
            if self.button_save_settings.is_pressed(mx, my):
                self.progress.save_settings(self.progress.keys, self.fps, self.audio.music_vol, self.audio.sfx_vol)

            if self.button_reset_settings.is_pressed(mx, my):
                self.fps = FPS
                self.audio.music_vol = DEFAULT_MUSIC_VOL
                self.audio.sfx_vol = DEFAULT_SFX_VOL
                self.audio.update_volume()
                self.progress.keys = {
                    "up": K_z,
                    "down": K_s,
                    "left": K_q,
                    "right": K_d,
                    "reset": K_r,
                    "music": K_e,
                    "menu": K_ESCAPE
                }

                # Texts
                self.sfx_vol = TextUI(
                    self.button_vol_sfx_right.centerx - 125, self.button_vol_sfx_left.centery, self.assets["font_medium"], str(int(100*self.audio.sfx_vol))+" %", (255, 255, 255)
                )
                self.music_vol = TextUI(
                    self.button_vol_music_right.centerx - 125, self.button_vol_music_left.centery, self.assets["font_medium"], str(int(100*self.audio.music_vol))+" %", (255, 255, 255)
                )
                self.fps_value = TextUI(
                    self.button_fps_arrow_right.centerx - 125, self.button_fps_arrow_left.centery, self.assets["font_medium"], str(self.fps), (255, 255, 255)
                )
            
    # ==================================================================
    # Update
    # ==================================================================

    def update(self):
        raw_dt = self.clock.tick(self.fps) / 1000.0
        self.dt = min(raw_dt, 0.05)
        x,y = self.player.x, self.player.y

        self.audio.update(self.dt)

        if self.state != GameState.MAZE:
            return

        self.seconds = round((pygame.time.get_ticks() - self.timer) / 1000, 2)
        keys = pygame.key.get_pressed()

        dx, dy = 0.0, 0.0
        dist = self.player.speed * self.dt
        if keys[self.progress.keys["left"]]: dx -= dist
        if keys[self.progress.keys["right"]]: dx += dist
        if keys[self.progress.keys["up"]]: dy -= dist
        if keys[self.progress.keys["down"]]: dy += dist

        # Obstacles = walls + closed doors (traps handled separately)
        walls = list(self.levels.walls(self.maze))
        for obj in self.levels.special_objs(self.maze):
            if isinstance(obj, Door) and not obj.opened:
                walls.append(obj)

        self.player.move(dx, dy, walls, self)

        # Update invincibility timers
        self.player.update_invincibility(self.dt)

        # Shadow system - Record player movement and update shadows
        if self.levels.shadow_enabled:
            current_time = self.seconds
            for shadow in self.shadows:
                shadow.record_player_movement(self.player, current_time)
                shadow.update(current_time)
                shadow.update_invincibility(self.dt)

        # Walking sfx
        if self.audio.music_play :
            if self.walk_timer <= 0.0 :
                if (x != self.player.x or y != self.player.y):
                    self.audio.play_sfx(self.audio.next_walk_sfx)
                    self.audio.decide_next_walk_sfx()
                    self.walk_timer = 0.3
            else :
                self.walk_timer -= self.dt

        # Update dynamic walls and handle push mechanics
        self._update_dynamic_walls()

        self._process_objects()
        self._process_enemies()
        
        # Process shadow collision with player
        if self.levels.shadow_enabled:
            for shadow in self.shadows:
                if shadow.is_touching(self.player) and shadow.can_damage_player():
                    self.player.take_enemy_damage()
                    shadow.apply_damage()
                    break
        
        # Check if player is dead
        if self.player.is_dead():
            self._respawn()

    def _process_objects(self):
        portal_contact = False

        for obj in list(self.levels.special_objs(self.maze)):
            # Portal
            if isinstance(obj, Portal) and obj.is_touched(self.player):
                portal_contact = True
                if self.player.can_teleport:
                    if obj.dest_id is not None and obj.id != obj.dest_id and self.audio.music_play :
                        self.audio.play_sfx("sfx_teleport")
                    self.player.use_portal(obj, self.levels.special_objs(self.maze))
                    self.player.can_teleport = False
                    break

            # Victory
            elif isinstance(obj, Winpad) and obj.is_touched(self.player) and not self.player.win:
                self._handle_victory()
                break

            # Key
            elif isinstance(obj, Key) and not obj.collected and obj.is_touched(self.player):
                if self.audio.music_play :
                    self.audio.play_sfx("sfx_key")
                self.player.pick_up_key(obj)

            # Door
            elif isinstance(obj, Door) and not obj.opened:
                if obj.rect.inflate(10, 10).colliderect(self.player.rect):
                    if obj.id in self.player.keys:
                        if self.audio.music_play :
                            self.audio.play_sfx("sfx_unlock")
                        obj.open()

            # Trap
            elif isinstance(obj, Trap):
                if obj.rect.colliderect(self.player.rect):
                    self.player.take_trap_damage()

            # Light
            elif isinstance(obj, Light):
                if obj.is_touched(self.player) and obj.cooldown == 0.0:
                    obj.collect()
                    if self.audio.music_play :
                        self.audio.play_sfx("sfx_light")
                    obj.cooldown = TORCH_TIME
                    self.levels.vision_radius += TORCH_EFFECT
                if 0.0 < obj.cooldown <= TORCH_TIME:
                    obj.cooldown -= self.dt
                    if obj.cooldown <= 0.0:
                        obj.cooldown = 0.0
                        self.levels.vision_radius -= TORCH_EFFECT
                        obj.respawn()
            
            # Heal
            elif isinstance(obj, Heal):
                if obj.is_touched(self.player) and self.player.health < PLAYER_HEALTH and not obj.collected:
                    obj.collect()
                    if self.audio.music_play :
                        self.audio.play_sfx("sfx_heal")
                    if self.player.health + HEAL_EFFECT <= 100:
                        self.player.health += HEAL_EFFECT
                    else :
                        self.player.health = PLAYER_HEALTH
            
            # Speed
            elif isinstance(obj, Speed):
                if obj.is_touched(self.player) and obj.cooldown == 0.0:
                    obj.collect()
                    if self.audio.music_play :
                        self.audio.play_sfx("sfx_speed")                    
                    obj.cooldown = 2*SPEED_TIME
                    self.player.speed += SPEED_EFFECT
                if 0.0 < obj.cooldown <= 2*SPEED_TIME:
                    obj.cooldown -= self.dt
                    if obj.cooldown <= 0.0:
                        obj.cooldown = 0.0
                        obj.respawn()
                    elif obj.cooldown <= SPEED_TIME and self.player.speed == PLAYER_SPEED + SPEED_EFFECT :
                        self.player.speed -= SPEED_EFFECT
            
            elif isinstance(obj, Shield):
                if obj.is_touched(self.player) and obj.cooldown == 0.0:
                    obj.collect()
                    if self.audio.music_play :
                        self.audio.play_sfx("sfx_shield")                    
                    obj.cooldown = 2*SHIELD_TIME
                    self.player.invicible = True
                if 0.0 < obj.cooldown <= 2*SHIELD_TIME:
                    obj.cooldown -= self.dt
                    if obj.cooldown <= 0.0:
                        obj.cooldown = 0.0
                        obj.respawn()
                    elif obj.cooldown <= SHIELD_TIME and self.player.invicible == True :
                        self.player.invicible = False

            # Sub-map
            elif isinstance(obj, SubMapPortal) and obj.is_touched(self.player):
                self.current_map_index = obj.target_map_index
                layout = self.levels.load_sub_map(self.maze, obj.target_map_index, self, False)
                self.player.teleport(
                    obj.spawn_pos[0] + self.player.width / 2,
                    obj.spawn_pos[1] + self.player.width / 2,
                )
                self._resize_window(layout)
                if self.audio.music_play :
                    self.audio.play_sfx("sfx_teleport")
                break

        if not portal_contact:
            self.player.can_teleport = True
        
        # Check if player is dead
        if self.player.is_dead():
            self._respawn()
    
    def _process_enemies(self):
        current_map = self.current_map_index  # index sub-map actif
        
        for enemy in self.levels.enemies(self.maze):
            if enemy.map_index != current_map:
                continue
            layout = self.levels.level_map_list[self.maze-1]
            enemy.update(self.player, self.levels.walls(self.maze), self.dt, layout, self.tile_size)
            
            # Check if enemy is touching player and apply damage
            # Use distance-based detection to handle cases where enemy stops before player
            if enemy.is_touching(self.player):
                self.player.take_enemy_damage()
        
        # Check if player is dead
        if self.player.is_dead():
            self._respawn()

    def _update_dynamic_walls(self):
        """Update dynamic walls and push player/enemies if touching."""
        current_map = self.current_map_index
        
        for obj in self.levels.special_objs(self.maze):
            if not isinstance(obj, DynamicWall):
                continue
            
            # Update wall position
            obj.update(self.dt)
            
            # Push player if touching
            if obj.rect.colliderect(self.player.rect.inflate(-2,-2)):
                push_dx, push_dy = obj.get_push_direction()
                push_amount = 150 * self.dt  # pixels per second
                push_x = push_dx * push_amount
                push_y = push_dy * push_amount
                # Try to push in the push direction
                walls = list(self.levels.walls(self.maze))
                for wall_obj in self.levels.special_objs(self.maze):
                    if isinstance(wall_obj, Door) and not wall_obj.opened:
                        walls.append(wall_obj)
                # Push player
                if (push_dx < 0 and obj.x >= self.player.x) or (push_dx > 0 and obj.x + obj.width/2 <= self.player.x):
                    self.player.x += push_x
                if (push_dy < 0 and obj.y >= self.player.y) or (push_dy > 0 and obj.y + obj.height/2 <= self.player.y):
                    self.player.y += push_y
                self.player.rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.width)
            
            # Push enemies if touching
            for enemy in self.levels.enemies(self.maze):
                if enemy.map_index != current_map:
                    continue
                
                if obj.rect.colliderect(enemy.rect):
                    push_dx, push_dy = obj.get_push_direction()
                    push_amount = 150 * self.dt  # pixels per second
                    push_x = push_dx * push_amount
                    push_y = push_dy * push_amount
                    # Push enemy in direction
                    walls = list(self.levels.walls(self.maze))
                    # Check collision with walls before pushing
                    if (push_dx < 0 and obj.x >= enemy.x) or (push_dx > 0 and obj.x + obj.width/2 <= enemy.x):
                        enemy.x += push_x
                    if (push_dy < 0 and obj.y >= enemy.y) or (push_dy > 0 and obj.y + obj.height/2 <= enemy.y):
                        enemy.y += push_y
                    
                    enemy.rect = pygame.Rect(int(enemy.x), int(enemy.y), enemy.width, enemy.width)

    # ==================================================================
    # Rendering
    # ==================================================================

    def render(self):
        # Background
        if self.maze == 67 or self.level_menu == 67:
            self.screen.fill(self.second_font_color)
        else:
            self.screen.fill(self.font_color)

        if self.state == GameState.MAZE:
            self._render_maze()
        elif self.state == GameState.LEVEL_MENU:
            self._render_level_menu()
        elif self.state in (GameState.FRENCH_TUTORIAL, GameState.ENGLISH_TUTORIAL):
            self._render_tutorial()
        elif self.state == GameState.VICTORY_MENU:
            self._render_victory()
        elif self.state == GameState.MAIN_MENU:
            self._render_main_menu()
        elif self.state == GameState.SETTINGS_MENU:
            self._render_settings()

        # Music icon animation
        if self.audio.music_animation:
            img_key = "music_on" if self.audio.music_play else "music_off"
            self.screen.blit(self.assets[img_key], (self.width - 75, 25))

        pygame.display.flip()

    def _render_maze(self):
        objs  = self.levels.special_objs(self.maze)
        walls = self.levels.walls(self.maze)

        # Special objects
        for obj in objs:
            if isinstance(obj, Portal):
                img = obj.img if obj.dest_id is not None else obj.img2
                self.screen.blit(img, (obj.x, obj.y))
            elif isinstance(obj, Winpad):
                self.screen.blit(obj.img, (obj.x, obj.y))
            elif isinstance(obj, Key) and not obj.collected:
                self.screen.blit(obj.img, (obj.x, obj.y))
            elif isinstance(obj, Door) and not obj.opened:
                color = KEY_COLORS.get(obj.id.lower(), DEFAULT_KEY_COLOR)
                pygame.draw.rect(self.screen, color, (obj.x1, obj.y1, obj.x2 - obj.x1, obj.y2 - obj.y1))
                pygame.draw.rect(self.screen, (0, 0, 0), obj.rect, 2)
            elif isinstance(obj, Trap):
                self.screen.blit(obj.img, (obj.x, obj.y))
            elif isinstance(obj, Light) and not obj.collected:
                self.screen.blit(obj.img, (obj.x, obj.y))
            elif isinstance(obj, Heal) and not obj.collected:
                self.screen.blit(obj.img, (obj.x, obj.y))
            elif isinstance(obj, Speed) and not obj.collected:
                self.screen.blit(obj.img, (obj.x, obj.y))
            elif isinstance(obj, Shield) and not obj.collected:
                self.screen.blit(obj.img, (obj.x,obj.y))
            elif isinstance(obj, SubMapPortal):
                self.screen.blit(obj.img, (obj.x, obj.y))
            elif isinstance(obj, DynamicWall):
                if obj.img and obj.wall_type == "vertical":
                    self.screen.blit(obj.img, (obj.x, obj.y))
                elif obj.img and obj.wall_type == "horizontal":
                    # Rotate the image 90 degrees for horizontal walls
                    rotated_img = pygame.transform.rotate(obj.img, -90)
                    # Adjust position to center the rotated image
                    self.screen.blit(rotated_img, (obj.x, obj.y))

        # Shadow (drawn before player so it appears below)
        if self.levels.shadow_enabled:
            for shadow in self.shadows:
                shadow_img = self.assets[f"shadow_{shadow.direction}"]
                self.screen.blit(shadow_img, (shadow.x, shadow.y))

        # Player
        player_img = self.assets[f"player_{self.player.direction}"]
        self.screen.blit(player_img,(self.player.x,self.player.y))

        # Enemy
        for enemy in self.levels.enemies(self.maze):
            if enemy.map_index == self.current_map_index:
                img = self.assets[f"enemy_{enemy.direction}"]
                self.screen.blit(img, (enemy.x, enemy.y))

        # Walls
        level_color = self.level_colors.get(self.maze, (255, 255, 255))
        for wall in walls:
            pygame.draw.rect(self.screen, level_color,
                             (wall.x1, wall.y1, wall.x2 - wall.x1, wall.y2 - wall.y1))

        # Shield (always around the player)
        if self.player.invicible :
            pygame.draw.circle(self.screen, (0,255,255), (self.player.x + self.player.width//2, self.player.y + self.player.width//2), 35.0, 2)

        # Fog of war
        if self.levels.has_fow(self.maze):
            self._draw_fog()

        # Render health bar
        self._render_health_bar()

        # Render timer
        timer_txt = TextUI(
            self.width-100, 30, self.assets["font_small"], f"Time : {self.seconds}", (255, 255, 255)
            )
        self.screen.blit(timer_txt.txt, timer_txt.pos)

    def _render_health_bar(self):
        """Render the player health bar at the top left of the screen"""
        # Health bar dimensions
        bar_width = 100
        bar_height = 20
        bar_x = 10
        bar_y = 10
        
        # Calculate health percentage
        health_percentage = max(0, self.player.health / self.player.max_health)
        green_width = int(bar_width * health_percentage)
        red_width = bar_width - green_width
        
        # Draw green part (current health)
        if green_width > 0:
            pygame.draw.rect(self.screen, (0, 255, 0), 
                           (bar_x, bar_y, green_width, bar_height))
        
        # Draw red part (missing health)
        if red_width > 0:
            pygame.draw.rect(self.screen, (255, 0, 0), 
                           (bar_x + green_width, bar_y, red_width, bar_height))
        
        # Draw border
        pygame.draw.rect(self.screen, (255, 255, 255), 
                       (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Draw health text
        health_text = TextUI(
            bar_x + bar_width + 50, bar_y + bar_height // 2, 
            self.assets["font_small"], 
            f"{int(self.player.health)}/100", 
            (255, 255, 255)
        )
        self.screen.blit(health_text.txt, health_text.pos)

    def _render_level_menu(self):
        font_color = self.font_color
        if self.level_menu == 67:
            font_color = invert_color(font_color)
        inv_color = invert_color(font_color)
        level_color = self.level_colors.get(self.level_menu, self.second_font_color)
        
        # Check if level is empty
        is_empty = self._is_level_empty(self.level_menu)
        alpha = 64 if is_empty else 255  # 25% opacity for empty levels

        level_btn = self.button_levels[self.level_menu - 1]
        
        # Draw button rectangles with alpha if empty level
        if is_empty:
            if self.level_menu == 67:
                level_color = (0,0,0)
            # Create temporary surface for button rectangles
            button_surface = pygame.Surface((int(level_btn.width), int(level_btn.height)), pygame.SRCALPHA)
            pygame.draw.rect(button_surface, (*level_color, alpha),
                           (0, 0, level_btn.width, level_btn.height))
            pygame.draw.rect(button_surface, (*font_color, alpha),
                           (20, 20, level_btn.width - 40, level_btn.height - 40))
            self.screen.blit(button_surface, (level_btn.x, level_btn.y))
        else:
            pygame.draw.rect(self.screen, level_color,
                           (level_btn.x, level_btn.y, level_btn.width, level_btn.height))
            pygame.draw.rect(self.screen, font_color,
                           (level_btn.x + 20, level_btn.y + 20,
                            level_btn.width - 40, level_btn.height - 40))

        t = self.level_texts[self.level_menu - 1]
        t_reduced = self._reduce_surface_alpha(t.txt, alpha) if is_empty else t.txt
        self.screen.blit(t_reduced, t.pos)

        play_t = TextUI(
            self.center_x, self.center_y, self.assets["font_main"], PLAY_TEXT, level_color
            )
        play_t_reduced = self._reduce_surface_alpha(play_t.txt, alpha) if is_empty else play_t.txt
        self.screen.blit(play_t_reduced, play_t.pos)

        stars = self.level_stars.get(self.level_menu, 0)
        star_txt = TextUI(
            self.center_x + 20, self.center_y + 200, self.assets["font_medium"], f": {stars}", inv_color
            )
        w, _ = star_txt.txt.get_size()
        
        star_reduced = self._reduce_surface_alpha(self.assets["star"], alpha) if is_empty else self.assets["star"]
        self.screen.blit(star_reduced, (self.center_x - 75, self.center_y + 175))
        
        star_txt_reduced = self._reduce_surface_alpha(star_txt.txt, alpha) if is_empty else star_txt.txt
        self.screen.blit(star_txt_reduced, (star_txt.pos.left + w / 2 - 25, star_txt.pos.top))

        if self.progress.is_completed(self.level_menu):
            completed_reduced = self._reduce_surface_alpha(self.assets["completed"], alpha) if is_empty else self.assets["completed"]
            self.screen.blit(completed_reduced, (self.center_x - 75, self.center_y + 175))

        rec_txt = TextUI(
            self.center_x, self.center_y + 275, self.assets["font_medium"], 
            f"Record : {self.progress.best_time_display(self.level_menu)}", inv_color
            )
        rec_txt_reduced = self._reduce_surface_alpha(rec_txt.txt, alpha) if is_empty else rec_txt.txt
        self.screen.blit(rec_txt_reduced, rec_txt.pos)

        if self.level_menu in self.level_names or self.level_menu in [67,69]:
            li_txt = TextUI(
                self.center_x, 100, self.assets["font_small"],
                f"Level {self.level_menu}",
                inv_color
            )
            li_txt_reduced = self._reduce_surface_alpha(li_txt.txt, alpha) if is_empty else li_txt.txt
            self.screen.blit(li_txt_reduced, li_txt.pos)

        # Render arrows (always full opacity)
        for btn in (self.button_left_arrow, self.button_right_arrow,
                    self.button_left_arrow2, self.button_right_arrow2):
            self.screen.blit(btn.img, (btn.x, btn.y))
        
        # Render "Coming soon..." for empty levels
        if is_empty:
            coming_soon_txt = TextUI(
                self.center_x, self.center_y, self.assets["font_medium"], 
                "Coming soon...", inv_color
            )
            self.screen.blit(coming_soon_txt.txt, coming_soon_txt.pos)

    def _render_tutorial(self):
        texts = (self.tutorial_fr if self.state == GameState.FRENCH_TUTORIAL
                 else self.tutorial_en)
        for t in texts:
            self.screen.blit(t.txt, t.pos)
        self.screen.blit(self.button_home.img, (self.button_home.x, self.button_home.y))

    def _render_victory(self):
        pygame.draw.rect(self.screen, (255, 255, 0), (50, 50, self.width - 100, self.height - 100))
        pygame.draw.rect(self.screen, (0, 0, 0),     (75, 75, self.width - 150, self.height - 150))
        self.screen.blit(self.victory_text.txt, self.victory_text.pos)
        self.screen.blit(self.button_home.img, (self.button_home.x, self.button_home.y))
        self.screen.blit(self.final_timer_text.txt, self.final_timer_text.pos)
        if self.display_record_txt:
            self.screen.blit(self.record_txt.txt, self.record_txt.pos)

    def _render_main_menu(self):
        self.screen.blit(self.name_text.txt, self.name_text.pos)
        pygame.draw.rect(self.screen, (255, 255, 0),
                         (self.button_start.x, self.button_start.y,
                          self.button_start.width, self.button_start.height))
        pygame.draw.rect(self.screen, (0, 0, 0),
                         (self.button_start.x + 10, self.button_start.y + 10,
                          self.button_start.width - 20, self.button_start.height - 20))
        self.screen.blit(self.start_text.txt, self.start_text.pos)
        self.screen.blit(self.button_book_fr.img, (self.button_book_fr.x, self.button_book_fr.y))
        self.screen.blit(self.button_book_en.img, (self.button_book_en.x, self.button_book_en.y))

        w, _ = self.stars_display.txt.get_size()
        self.screen.blit(self.assets["star"], (25, 25))
        self.screen.blit(self.stars_display.txt, (self.stars_display.pos.left + w / 2, self.stars_display.pos.top))
        self.screen.blit(self.v_txt.txt, self.v_txt.pos)

        self.screen.blit(self.button_settings.img,(self.button_settings.x,self.button_settings.y))
    
    def _render_settings(self):
        self.screen.blit(self.settings_txt.txt, self.settings_txt.pos)
        self.screen.blit(self.button_home.img, (self.button_home.x, self.button_home.y))

        # FPS section
        self.screen.blit(self.fps_label.txt, self.fps_label.pos)
        self.screen.blit(self.button_fps_arrow_left.img, (self.button_fps_arrow_left.x, self.button_fps_arrow_left.y))
        self.screen.blit(self.button_fps_arrow_right.img, (self.button_fps_arrow_right.x, self.button_fps_arrow_right.y))
        self.screen.blit(self.fps_value.txt, self.fps_value.pos)

        # Music section
        self.screen.blit(self.music_label.txt, self.music_label.pos)
        self.screen.blit(self.button_vol_music_left.img, (self.button_vol_music_left.x, self.button_vol_music_left.y))
        self.screen.blit(self.button_vol_music_right.img, (self.button_vol_music_right.x, self.button_vol_music_right.y))
        self.screen.blit(self.music_vol.txt, self.music_vol.pos)

        # SFX section
        self.screen.blit(self.sfx_label.txt, self.sfx_label.pos)
        self.screen.blit(self.button_vol_sfx_left.img, (self.button_vol_sfx_left.x, self.button_vol_sfx_left.y))
        self.screen.blit(self.button_vol_sfx_right.img, (self.button_vol_sfx_right.x, self.button_vol_sfx_right.y))
        self.screen.blit(self.sfx_vol.txt, self.sfx_vol.pos)

        # Key bindings section
        self.screen.blit(self.key_title.txt, self.key_title.pos)
        pygame.draw.rect(self.screen,(255,255,0),(self.key_title.centerx-400,self.key_title.centery,200,2))
        pygame.draw.rect(self.screen, (255,255,0), (self.key_title.centerx + 200, self.key_title.centery, 200, 2))

        binding_labels = {
            "up": "Up",
            "down": "Down",
            "left": "Left",
            "right": "Right",
            "reset": "Reset",
            "menu": "Menu"
        }

        for binding_name, button in self.button_key_bindings.items():
            color = (255,0,0) if binding_name == self.binding_action else (255,255,0)
            label_text = TextUI(
                button.x - 80, button.centery, self.assets["font_small"], binding_labels[binding_name], (255, 255, 255)
            )
            self.screen.blit(label_text.txt, label_text.pos)
            pygame.draw.rect(self.screen, color,
                             (button.x, button.y, button.width, button.height), 2)
            key_code = self.progress.keys.get(binding_name, "")
            display_key = pygame.key.name(key_code).upper()
            if binding_name == self.binding_action :
                display_key = "..."
            elif key_code == 27 :
                display_key = "ESCAPE"
            item_text = TextUI(
                button.centerx, button.centery, self.assets["font_small"], display_key, (255, 255, 255)
            )
            self.screen.blit(item_text.txt, item_text.pos)

        # Save button
        pygame.draw.rect(self.screen,(255,255,0),(self.center_x-100,HEIGHT_SETTINGS-75,200,50))
        self.screen.blit(self.save_text.txt, self.save_text.pos)

        # Reset button
        pygame.draw.rect(self.screen, (0, 0, 0), (self.button_reset_settings.x, self.button_reset_settings.y, self.button_reset_settings.width, self.button_reset_settings.height))
        pygame.draw.rect(self.screen, (255, 0, 0), (self.button_reset_settings.x, self.button_reset_settings.y, self.button_reset_settings.width, self.button_reset_settings.height), 2)
        self.screen.blit(self.reset_text.txt, self.reset_text.pos)

    # ==================================================================
    # Transitions // actions
    # ==================================================================

    def fade_to_black(self, width, height, speed=10):
        surf = pygame.Surface((width, height))
        surf.fill((0, 0, 0))
        for alpha in range(0, 256, speed):
            surf.set_alpha(alpha)
            self.screen.blit(surf, (0, 0))
            pygame.display.update()
            pygame.time.delay(28)

    def _draw_fog(self):
        fog = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        fog.fill((0, 0, 0, 255))
        r = self.levels.vision_radius
        for i in range(r, 0, -5):
            alpha = int(255 * (i / r))
            pygame.draw.circle(fog, (0, 0, 0, alpha), self.player.rect.center, i)
        self.screen.blit(fog, (0, 0))

    def _go_to_menu(self):
        if self.state == GameState.MAZE:
            self.levels.reset_objects(self.maze)
        self.player.reset()
        self.state = GameState.MAIN_MENU
        self.maze = 0
        self.level_menu = 0
        self.display_record_txt = False
        self.levels.reset_vision()
        self.timer = pygame.time.get_ticks()
        
        self.fade_to_black(self.width, self.height, self.fade_speed["normal"])

        self.width, self.height = self.default_window_size
        self.screen = pygame.display.set_mode(self.default_window_size)
        self.center_x = self.screen.get_rect().centerx
        self.center_y = self.screen.get_rect().centery

        self.stars_display = TextUI(
            100, 50, self.assets["font_medium"], str(self.progress.nb_stars), (255, 255, 255)
        )

        self.audio.switch_to_menu()
        self.clock.tick()

    def _respawn(self):
        self.levels.reset_objects(self.maze)
        self.levels.reset_vision()
        if self.audio.music_play :
            self.audio.play_sfx("sfx_death")
        for e in self.levels.enemies(self.maze):
            e.reset()
        self.current_map_index = 0
        layout = self.levels.load_sub_map(self.maze, 0, self, False)
        self.player.respawn()
        for shadow in self.shadows:
            shadow.reset()
        self._resize_window(layout)
        self.timer = pygame.time.get_ticks()
        self.clock.tick()

    def _handle_victory(self):
        if self.audio.music_play :
            self.audio.play_sfx("sfx_win")
        self.player.victory()
        self.fade_to_black(self.width, self.height, self.fade_speed["slow"])

        stars = self.level_stars.get(self.maze, 0)
        new_record = self.progress.record_victory(self.maze, stars, self.seconds)
        self.display_record_txt = new_record

        self.audio.switch_to_victory()

        self.width, self.height = self.default_window_size
        self.screen = pygame.display.set_mode(self.default_window_size)
        self.center_x = self.screen.get_rect().centerx
        self.center_y = self.screen.get_rect().centery

        self.final_timer_text = TextUI(
            self.center_x, self.center_y, self.assets["font_main"],
            f"Time : {self.seconds}", (255, 255, 255)
        )
        self.state = GameState.VICTORY_MENU
        self.maze = 0

    def _start_level(self, level_id: int):
        self.state      = GameState.MAZE
        self.level_menu = 0
        self.maze       = level_id
        self.current_map_index = 0
        self.display_record_txt = False

        if self.audio.music_play :
            self.audio.play_sfx("sfx_play")
        self.fade_to_black(self.width, self.height, self.fade_speed["normal"])
        self.screen.blit(self.loading_text.txt, self.loading_text.pos)
        pygame.display.flip()

        cfg = self.levels.level_configs.get(level_id)
        if cfg:
            if not cfg["loaded"] and level_id != 3:
                layout = self.levels.load_level(level_id, self)
            else:
                layout = self.levels.load_sub_map(level_id, 0, self, True)
            self._resize_window(layout)

        # Initialize shadows if enabled for this level
        shadow_count = self.levels.get_shadow_count(level_id)
        self.levels.shadow_enabled = shadow_count > 0
        self.shadows = [
            Shadow(self.assets["shadow"], SHADOW_DELAY + i)
            for i in range(shadow_count)
        ]
        self.levels.shadows = self.shadows
        for shadow in self.shadows:
            shadow.reset()
        self.shadow_start_time = 0.0

        self.audio.switch_to_level(level_id)
        self.timer = pygame.time.get_ticks()
        self.clock.tick()

    def _resize_window(self, layout):
        self.fade_to_black(self.width, self.height, self.fade_speed["normal"])
        self.width  = len(layout[0]) * self.tile_size
        self.height = len(layout)    * self.tile_size
        os.environ["SDL_VIDEO_WINDOW_POS"] = "center"
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock.tick()

    def _is_level_empty(self, level_id: int) -> bool:
        """Check if a level has a valid configuration."""
        cfg = self.levels.level_configs.get(level_id)
        return cfg is None

    def _reduce_surface_alpha(self, surface: pygame.Surface, alpha: int) -> pygame.Surface:
        """Create a copy of the surface with reduced alpha (0-255)."""
        # Convert to alpha format and apply alpha
        new_surface = surface.convert_alpha()
        new_surface.set_alpha(alpha)
        return new_surface

    # ==================================================================
    # Level menu navigation
    # ==================================================================

    def _press_left(self):
        self.level_menu = self.nb_levels if self.level_menu == 1 else self.level_menu - 1

    def _press_right(self):
        self.level_menu = 1 if self.level_menu == self.nb_levels else self.level_menu + 1

    def _jump_left(self):
        self.level_menu = max(1, self.level_menu - 10)

    def _jump_right(self):
        self.level_menu = min(self.nb_levels, self.level_menu + 10)

    # ==================================================================
    # UI Construction
    # ==================================================================

    def _build_ui(self):
        a = self.assets
        cx, cy = self.center_x, self.center_y

        self.name_text = TextUI(cx, cy - 200, a["font_main"], GAME_NAME, (255, 255, 255))
        self.start_text = TextUI(cx, cy, a["font_main"], START_TEXT, (255, 255, 0))
        self.victory_text = TextUI(cx, cy // 2, a["font_main"], VICTORY_TEXT, (255, 255, 0))
        self.stars_display = TextUI(100, 50, a["font_medium"], str(self.progress.nb_stars), (255, 255, 255))
        self.v_txt = TextUI(2*cx -25 -6*len(GAME_VERSION), 25, a["font_small"], GAME_VERSION, (255, 255, 255))
        self.record_txt = TextUI(cx, cy + 75, a["font_medium"], RECORD_TEXT, (255, 255, 255))
        self.settings_txt = TextUI(cx, 100, a["font_main"], SETTINGS_TITLE, (255, 255, 0))
        self.display_record_txt = False

        self.fps_label = TextUI(
            130, self.settings_txt.centery + 100, self.assets["font_medium"], "FPS", (255, 255, 0)
        )
        self.music_label = TextUI(
            130, self.fps_label.centery + 75, self.assets["font_medium"], "Music", (255, 255, 0)
        )
        self.sfx_label = TextUI(
            130, self.music_label.centery + 75, self.assets["font_medium"], "SFX", (255, 255, 0)
        )
        self.key_title = TextUI(
            self.center_x, self.sfx_label.centery + 100, self.assets["font_medium"], "Key Bindings", (255, 255, 0)
        )


        # Level texts
        self.level_texts = [
            TextUI(cx, cy - 200, a["font_main"], f"Level {n + 1}", (255, 255, 255)) for n in range(NB_LEVELS)
        ]
        color =  self.second_font_color
        for lvl_id, name in self.level_names.items():
            self.level_texts[lvl_id - 1] = TextUI(cx, cy - 200, a["font_main"], name, color)
        self.level_texts[66] = TextUI(cx, cy - 200, a["font_main"], "heheheha", invert_color(color))
        self.level_texts[68] = TextUI(cx, cy - 200, a["font_main"], "Nice", color)

        # Tutorials
        self.tutorial_fr = [
            TextUI(cx, TILE_SIZE * (i + 2), a["font_small"], txt, (255, 255, 255))
            for i, txt in enumerate(TUTORIAL_FR_TEXT)
        ]
        self.tutorial_en = [
            TextUI(cx, TILE_SIZE * (i + 2), a["font_small"], txt, (255, 255, 255))
            for i, txt in enumerate(TUTORIAL_EN_TEXT)
        ]

        # Placeholder for level end text
        self.final_timer_text = TextUI(cx, cy + 50, a["font_medium"], "", (255, 255, 255))

        # Buttons
        self.button_start        = ButtonUI(cx, cy, 400, 150, None)
        self.button_book_fr      = ButtonUI(100, self.height - 100, 100, 100, a["tutorial_fr"])
        self.button_book_en      = ButtonUI(250, self.height - 100, 100, 100, a["tutorial_en"])
        self.button_right_arrow  = ButtonUI(self.width - 100, cy - 50, 50, 50, a["right_arrow"])
        self.button_left_arrow   = ButtonUI(100, cy - 50, 50, 50, a["left_arrow"])
        self.button_right_arrow2 = ButtonUI(self.width - 100, cy + 50, 50, 50, a["right_double_arrow"])
        self.button_left_arrow2  = ButtonUI(100, cy + 50, 50, 50, a["left_double_arrow"])
        self.button_home         = ButtonUI(50, 50, 75, 75, a["home"])
        self.button_levels       = [ButtonUI(cx, cy, 400, 250, None) for _ in range(NB_LEVELS)]
        self.button_settings     = ButtonUI(self.width - 100, self.height - 100, 50, 50, a["settings"])
        self.button_music        = ButtonUI(cx - 250, cy - 75, 120, 120, a["music_on"])

        self.button_fps_arrow_left  = ButtonUI(cx + 100, self.fps_label.centery, 50, 50, a["left_arrow"])
        self.button_fps_arrow_right = ButtonUI(self.button_fps_arrow_left.centerx + 250, self.fps_label.centery, 50, 50, a["right_arrow"])
        self.button_vol_music_left  = ButtonUI(cx + 100, self.music_label.centery, 50, 50, a["left_arrow"])
        self.button_vol_music_right = ButtonUI(self.button_vol_music_left.centerx + 250, self.music_label.centery, 50, 50, a["right_arrow"])
        self.button_vol_sfx_left    = ButtonUI(cx + 100, self.sfx_label.centery, 50, 50, a["left_arrow"])
        self.button_vol_sfx_right   = ButtonUI(self.button_vol_sfx_left.centerx + 250, self.sfx_label.centery, 50, 50, a["right_arrow"])

        self.fps_value = TextUI(
            self.button_fps_arrow_right.centerx - 125, self.button_fps_arrow_left.centery, self.assets["font_medium"], str(self.fps), (255, 255, 255)
        )
        self.music_vol = TextUI(
            self.button_vol_music_right.centerx - 125, self.button_vol_music_left.centery, self.assets["font_medium"], str(int(100*self.audio.music_vol))+" %", (255,255,255)
        )
        self.sfx_vol = TextUI(
            self.button_vol_sfx_right.centerx - 125, self.button_vol_sfx_left.centery, self.assets["font_medium"], str(int(100*self.audio.sfx_vol))+" %", (255,255,255)
        )

        right_col = self.fps_value.centerx
        left_col = cx - 150
        y_level = self.key_title.centery + 80

        self.button_key_bindings = {
            "up":     ButtonUI(left_col, y_level, 120, 50, None),
            "down":   ButtonUI(right_col, y_level, 120, 50, None),
            "left":   ButtonUI(left_col, y_level+80, 120, 50, None),
            "right":  ButtonUI(right_col, y_level+80, 120, 50, None),
            "reset":  ButtonUI(left_col, y_level+160, 120, 50, None),
            "menu":   ButtonUI(right_col, y_level+160, 120, 50, None),
        }

        self.button_reset_settings = ButtonUI(cx - 200, HEIGHT_SETTINGS-50, 100, 50, None)
        self.button_save_settings = ButtonUI(cx, HEIGHT_SETTINGS-50, 100, 50, None)
        self.save_text = TextUI(self.button_save_settings.centerx,self.button_save_settings.centery, self.assets["font_small"], SAVE_TEXT, (0,0,0))

        self.reset_text = TextUI(self.button_reset_settings.centerx, self.button_reset_settings.centery, self.assets["font_small"], RESET_TEXT, (255, 0, 0))