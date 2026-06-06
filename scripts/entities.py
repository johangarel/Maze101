import pygame
from .settings import (TILE_SIZE, TORCH_EFFECT, KEY_COLORS, 
                       PLAYER_WIDTH, INVICIBILITY_TIME, SHADOW_DELAY, 
                       HEAL_EFFECT, SPEED_EFFECT, PLAYER_HEALTH, PLAYER_SPEED)


# ==================================================================
# Player class
# ==================================================================

class Player:
    def __init__(self,pos: tuple,speed: int,width: int, img):
        self.x, self.y = pos
        self.default_pos = pos
        self.respawn_pos = pos
        self.speed = speed
        self.width = width
        self.win = False
        self.keys = []
        self.rect = pygame.Rect(self.x,self.y,width,width)
        self.img = img
        self.can_teleport = False
        self.direction = "right"
        # Health system
        self.health = PLAYER_HEALTH
        self.max_health = PLAYER_HEALTH
        self.trap_invincibility_timer = 0.0
        self.enemy_invincibility_timer = 0.0
        self.INVINCIBILITY_DURATION = INVICIBILITY_TIME  # seconds

    def modify_speed(self,speed: int):
        self.speed = speed
    
    def is_in_bounds_vertical(self,dy: int,game) -> bool:
        return self.y + dy > 0 and self.y + self.width + dy < game.height

    def is_in_bounds_horizontal(self,dx: int,game) -> bool:
        return self.x + dx > 0 and self.x + self.width + dx < game.width

    def can_move(self, dx: int, dy: int, walls, game) -> bool:
        future_rect = pygame.Rect(self.x + dx, self.y + dy, self.width, self.width)
        
        for wall in walls:
            if future_rect.colliderect(wall.rect):
                return False
        
        # Check collision with enemies
        for enemy in game.levels.enemies(game.maze):
            if enemy.rect.colliderect(future_rect):
                return False
        
        # Check collision with traps
        for obj in game.levels.special_objs(game.maze):
            rect2 = future_rect.inflate(-2,-2)
            if obj.__class__.__name__ == 'Trap' and obj.rect.colliderect(rect2):
                return False
            if obj.__class__.__name__ == 'DynamicWall' and obj.rect.colliderect(future_rect):
                return False
            
        if not self.is_in_bounds_horizontal(dx, game):
            return False
        if not self.is_in_bounds_vertical(dy, game):
            return False

        return True

    def move(self,dx: int,dy: int,walls,game):
        assert isinstance(walls,list)

        if self.win :
            return
        
        # Update direction
        if  dx > 0:  self.direction = "right"
        elif  dx < 0: self.direction = "left"
        elif  dy < 0: self.direction = "up"
        elif  dy > 0: self.direction = "down"

        # horizontal
        if dx != 0:
            if self.can_move(dx, 0, walls, game):
                self.x += dx
            else: # To stick the player to the wall
                if dx > 0 :
                    direction = 1
                else :
                    direction = -1
                while self.can_move(direction, 0, walls, game) and abs(dx) > 1:
                    self.x += direction
                    dx -= direction
            

        #vertical
        if dy != 0:
            if self.can_move(0, dy, walls, game):
                self.y += dy
            else: # To stick the player to the wall
                if dy > 0 :
                    direction = 1
                else :
                    direction = -1
                while self.can_move(0, direction, walls, game) and abs(dy) > 1:
                    self.y += direction
                    dy -= direction
        
        self.rect = pygame.Rect(self.x,self.y,self.width,self.width)

    def move_spawn(self,x,y):
        if x != None and y != None :
            self.x = x
            self.y = y
            self.respawn_pos = (x,y)
            self.rect = pygame.Rect(self.x,self.y,self.width,self.width)

    def teleport(self,x,y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x,self.y,self.width,self.width)

    def use_portal(self, portal, objects_in_level):
        dest_portal = None
        for so in objects_in_level:
            # Searching the right portal
            if isinstance(so, Portal) and so != portal and so.id == portal.dest_id:
                dest_portal = so
                break

        if dest_portal:
            # Move player
            self.x = dest_portal.x + (dest_portal.width // 2) - (self.width // 2)
            self.y = dest_portal.y + (dest_portal.width // 2) - (self.width // 2)
            self.rect.topleft = (self.x, self.y)
    
    def victory(self):
        self.win = True

    def reset(self):
        self.win = False
        x,y = self.default_pos
        self.x = x
        self.y = y
        self.respawn_pos = (x,y)
        self.keys = []
        self.speed = PLAYER_SPEED
        self.rect = pygame.Rect(self.x,self.y,self.width,self.width)
        self.direction = "right"
        self.health = self.max_health
        self.trap_invincibility_timer = 0.0
        self.enemy_invincibility_timer = 0.0

    def respawn(self):
        x,y = self.respawn_pos
        self.x = x
        self.y = y
        self.keys = []
        self.speed = PLAYER_SPEED
        self.rect = pygame.Rect(self.x,self.y,self.width,self.width)
        self.health = self.max_health
        self.trap_invincibility_timer = 0.0
        self.enemy_invincibility_timer = 0.0

    def pick_up_key(self,key):
        assert isinstance(key,Key)
        self.keys.append(key.door_id)
        key.collect()

    def take_trap_damage(self):
        if self.trap_invincibility_timer <= 0:
            self.health = max(0, self.health - 50)
            self.trap_invincibility_timer = self.INVINCIBILITY_DURATION

    def take_enemy_damage(self):
        if self.enemy_invincibility_timer <= 0:
            self.health = max(0, self.health - 25)
            self.enemy_invincibility_timer = self.INVINCIBILITY_DURATION

    def update_invincibility(self, dt: float):
        if self.trap_invincibility_timer > 0:
            self.trap_invincibility_timer -= dt
        if self.enemy_invincibility_timer > 0:
            self.enemy_invincibility_timer -= dt

    def is_dead(self) -> bool:
        return self.health <= 0

# ==================================================================
# Eneny class
# ==================================================================

class Enemy:

    def __init__(self, x, y, patrol_path: list, speed_patrol: int, speed_chase: int, detection_radius: int, img, map_index: int):
        self.x, self.y = float(x), float(y)
        self.spawn_pos = (float(x), float(y))
        self.width = PLAYER_WIDTH
        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.width)

        # Patrol
        self.waypoints   = patrol_path   # list of (px_x, px_y)
        self.patrol_index  = 0
        self._was_chasing = False
        self._patrol_path = []         # list of pixel (x, y) waypoints
        self._patrol_path_timer = 0.0  # countdown to next recalculation
        self.PATROL_PATH_REFRESH = 0.6 # seconds between A* recalculations

        # A* chase path
        self._chase_path  = []   # list of pixel (x, y) waypoints
        self._path_timer  = 0.0  # countdown to next recalculation
        self.PATH_REFRESH = 0.6  # seconds between A* recalculations
        self._path_computed_this_cycle = False

        # Stats
        self.speed_patrol      = speed_patrol
        self.speed_chase       = speed_chase
        self.detection_radius  = detection_radius

        # Rendering
        self.img       = img
        self.direction = "right"
        self.map_index = map_index

        self.state = "patrol"  # "patrol" | "chase"
 
    def update(self, player, walls: list, dt: float, layout: list, tile_size: int) -> None:
        dist = self._distance_to(player)

        if self.state == "patrol":
            if dist <= self.detection_radius:
                self.state = "chase"
        else:  # chase
            if dist > self.detection_radius * 1.2:
                self.state = "patrol"

        if self.state == "chase":
            self._update_chase(player, walls, dt, layout, tile_size)
            self._was_chasing = True
        else:
            self._chase_path = []
            self._path_timer = 0.0
            if not self.waypoints:
                self._was_chasing = False
                return

            if self._was_chasing:
                self._patrol_path = []
                self._patrol_path_timer = 0.0
            self._was_chasing = False

            self._update_patrol(walls, dt, layout, tile_size)

    def _update_chase(self, player, walls: list, dt: float, layout: list, tile_size: int) -> None:
        """Follow the player using A* pathfinding."""
        from .utils import astar

        dist = self._distance_to(player)
        # Short distance chase
        if dist < 34.5:
            self._chase_path = []
            self._path_timer = self.PATH_REFRESH # reset timer
            self._path_computed_this_cycle = False
            self._move_towards(player.x, player.y, self.speed_chase, walls, player, dt)
            return

        self._path_timer -= dt
        if self._path_timer <= 0:
            start_col = int(self.x // tile_size)
            start_row = int(self.y // tile_size)
            start_snapped = (
                start_col * tile_size + tile_size // 2,
                start_row * tile_size + tile_size // 2,
            )
            self._chase_path = astar(
                layout,
                start_snapped,
                (player.x, player.y),
                tile_size,
            )
            self._path_timer = self.PATH_REFRESH

        if not self._chase_path and not self._path_computed_this_cycle:
            start_col = int(self.x // tile_size)
            start_row = int(self.y // tile_size)
            start_snapped = (
                start_col * tile_size + tile_size // 2,
                start_row * tile_size + tile_size // 2,
            )
            self._chase_path = astar(
                layout,
                start_snapped,
                (player.x, player.y),
                tile_size,
            )
            self._path_computed_this_cycle = True

        if self._chase_path:
            cx = self._chase_path[0][0] + tile_size // 2 - self.width // 2
            cy = self._chase_path[0][1] + tile_size // 2 - self.width // 2
            self._move_towards(cx, cy, self.speed_chase, walls, player, dt)
            if abs(self.x - cx) < 4 and abs(self.y - cy) < 4:
                self._chase_path.pop(0)
        else:
            self._update_patrol(walls, dt, layout, tile_size)

    def _update_patrol(self, walls: list, dt: float, layout: list, tile_size: int) -> None:
        from .utils import astar

        tx, ty = self.waypoints[self.patrol_index]

        # Waypoints
        if abs(self.x - tx) < 4 and abs(self.y - ty) < 4:
            self.patrol_index = (self.patrol_index + 1) % len(self.waypoints)
            self._patrol_path = []
            self._patrol_path_timer = 0.0
            tx, ty = self.waypoints[self.patrol_index]

        # A*
        self._patrol_path_timer -= dt
        if self._patrol_path_timer <= 0 or not self._patrol_path:
            self._patrol_path = astar(layout, (self.x, self.y), (tx, ty), tile_size)
            self._patrol_path_timer = self.PATROL_PATH_REFRESH

        if self._patrol_path:
            cx = self._patrol_path[0][0] + tile_size // 2 - self.width // 2
            cy = self._patrol_path[0][1] + tile_size // 2 - self.width // 2
            self._move_towards(cx, cy, self.speed_patrol, walls, None, dt)
            if abs(self.x - cx) < 4 and abs(self.y - cy) < 4:
                self._patrol_path.pop(0)
        else:
            # Fallback
            self._move_towards(tx, ty, self.speed_patrol, walls, None, dt)

    def is_touching(self, player) -> bool:
        # Use both rect collision and distance-based detection
        # This ensures damage is applied even if enemy stops just before player
        if self.rect.colliderect(player.rect):
            return True
        
        # Distance-based detection for cases where enemy is blocked just before touching
        dx = (self.x + self.width / 2) - (player.x + player.width / 2)
        dy = (self.y + self.width / 2) - (player.y + player.width / 2)
        distance = (dx ** 2 + dy ** 2) ** 0.5
        collision_distance = (self.width + player.width) / 2 + 5  # Add 5px tolerance
        
        return distance <= collision_distance

    def reset(self) -> None:
        self.x, self.y    = self.spawn_pos
        self.patrol_index = 0
        self.state        = "patrol"
        self._chase_path  = []
        self._path_timer  = 0.0
        self.rect         = pygame.Rect(int(self.x), int(self.y), self.width, self.width)
        self._was_chasing = False
        self._patrol_path = []
        self._patrol_path_timer = 0.0

    def _distance_to(self, player) -> float:
        dx = (self.x + self.width / 2) - (player.x + player.width / 2)
        dy = (self.y + self.width / 2) - (player.y + player.width / 2)
        return (dx ** 2 + dy ** 2) ** 0.5

    def _move_towards(self, tx: float, ty: float, speed: int, walls: list, player, dt: float) -> None:
        dx = tx - self.x
        dy = ty - self.y
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist < 1:
            return

        step      = speed * dt
        norm_dx   = dx / dist * min(step, dist)
        norm_dy   = dy / dist * min(step, dist)

        # Update sprite direction
        if abs(norm_dx) > abs(norm_dy):
            self.direction = "right" if norm_dx > 0 else "left"
        else:
            self.direction = "down" if norm_dy > 0 else "up"

        # Move axes independently so the enemy slides along walls
        future_x = pygame.Rect(int(self.x + norm_dx), int(self.y), self.width, self.width)
        future_y = pygame.Rect(int(self.x), int(self.y + norm_dy), self.width, self.width)

        # Check collision with walls
        player_rect = pygame.Rect(int(player.x), int(player.y), player.width, player.width) if player else None
        
        if not any(future_x.colliderect(w.rect) for w in walls) and (player_rect is None or not future_x.colliderect(player_rect)):
            self.x += norm_dx
        if not any(future_y.colliderect(w.rect) for w in walls) and (player_rect is None or not future_y.colliderect(player_rect)):
            self.y += norm_dy

        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.width)

    def _nearest_patrol_index(self) -> int:
        best_idx = self.patrol_index
        best_dist = float("inf")
        for i, (px, py) in enumerate(self.waypoints):
            d = (self.x - px) ** 2 + (self.y - py) ** 2
            if d < best_dist:
                best_dist = d
                best_idx = i
        return best_idx

# ==================================================================
# Shadow class
# ==================================================================

class Shadow:
    def __init__(self, img):
        from collections import deque
        self.x = -100.0 # Not on the screen by default
        self.y = -100.0
        self.width = PLAYER_WIDTH
        self.direction = "right"
        self.img = img
        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.width)
        
        # History of player positions with timestamps
        # Each entry: (x, y, direction, timestamp)
        self.position_history = deque(maxlen=1000)
        
        # Delay in seconds
        self.delay = SHADOW_DELAY
        
        # Collision tracking
        self.shadow_invincibility_timer = 0.0
        self.INVINCIBILITY_DURATION = INVICIBILITY_TIME  # seconds
    
    def record_player_movement(self, player, current_time: float) -> None:
        self.position_history.append((player.x, player.y, player.direction, current_time))
    
    def update(self, current_time: float) -> None:
        # Look for position from 3 seconds ago
        target_time = current_time - self.delay
        
        # Find the closest position in history before target_time
        found_pos = None
        for i in range(len(self.position_history) - 1, -1, -1):
            x, y, direction, timestamp = self.position_history[i]
            if timestamp <= target_time:
                found_pos = (x, y, direction)
                break
        
        # Update position and direction if found
        if found_pos:
            self.x, self.y, self.direction = found_pos
            self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.width)
        # If not found yet (within first 3 seconds), stay at initial position
    
    def is_touching(self, player) -> bool:
        if self.rect.colliderect(player.rect):
            return True
        
        # Distance-based detection
        dx = (self.x + self.width / 2) - (player.x + player.width / 2)
        dy = (self.y + self.width / 2) - (player.y + player.width / 2)
        distance = (dx ** 2 + dy ** 2) ** 0.5
        collision_distance = (self.width + player.width) / 2 + 5
        
        return distance <= collision_distance
    
    def reset(self) -> None:
        self.position_history.clear()
        self.x = -100.0
        self.y = -100.0
        self.direction = "right"
        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.width)
        self.shadow_invincibility_timer = 0.0
    
    def update_invincibility(self, dt: float) -> None:
        if self.shadow_invincibility_timer > 0:
            self.shadow_invincibility_timer -= dt
    
    def can_damage_player(self) -> bool:
        return self.shadow_invincibility_timer <= 0
    
    def apply_damage(self) -> None:
        self.shadow_invincibility_timer = self.INVINCIBILITY_DURATION

# ==================================================================
# Obstacles classes
# ==================================================================

class Wall :
    def __init__(self, x, y, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.x1, self.y1 = x, y
        self.x2, self.y2 = x + width, y + height

class DynamicWall:
    """A wall that moves between two positions and pushes the player/enemies."""
    
    def __init__(self, x1, y1, x2, y2, wall_type, img):
        self.wall_type = wall_type
        self.img = img
        
        # Dimensions
        if wall_type == "vertical":
            self.width = 40
            self.height = 10
        else:  # horizontal
            self.width = 10
            self.height = 40
        
        # Position and movement
        self.x = x1
        self.y = y1
        self.start_x = x1
        self.start_y = y1
        self.end_x = x2
        self.end_y = y2
        
        # Movement parameters
        self.speed = 100  # pixels per second
        self.direction = 1  # 1 or -1 for forward/backward
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # Calculate total distance
        self.total_distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if self.total_distance == 0:
            self.total_distance = 1  # Avoid division by zero
    
    def update(self, dt: float) -> None:
        """Update position of the dynamic wall."""
        if self.total_distance <= 0:
            return
        
        # Current distance from start
        curr_dist = ((self.x - self.start_x) ** 2 + (self.y - self.start_y) ** 2) ** 0.5
        
        # Move
        movement = self.speed * dt * self.direction
        next_dist = curr_dist + movement
        
        # Bounce at boundaries
        if next_dist <= 0:
            self.direction = 1
            next_dist = 0
        elif next_dist >= self.total_distance:
            self.direction = -1
            next_dist = self.total_distance
        
        # Set position based on progress
        if self.total_distance > 0:
            progress = next_dist / self.total_distance
            self.x = self.start_x + (self.end_x - self.start_x) * progress
            self.y = self.start_y + (self.end_y - self.start_y) * progress
        
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_push_direction(self):
        """Return the direction to push entities (normalized)."""
        if self.total_distance == 0:
            return (0, 0)
        
        dx = self.end_x - self.start_x
        dy = self.end_y - self.start_y
        dist = (dx ** 2 + dy ** 2) ** 0.5
        
        if dist == 0:
            return (0, 0)
        
        # Reverse direction if moving backward
        push_dir = -1 if self.direction == -1 else 1
        return (dx / dist * push_dir, dy / dist * push_dir)

class Door :
    def __init__(self,x,y,width: int,height: int,id=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.x1, self.y1 = x, y
        self.x2, self.y2 = x + width, y + height
        self.opened = False
        self.id = id.lower()
    
    def open(self):
        self.opened = True
    
    def reset(self):
        self.opened = False

# ==================================================================
# Triggers classes
# ==================================================================

class Winpad:
    def __init__(self,x,y,img):
        self.x = x
        self.y = y
        self.width = 50
        self.rect = pygame.Rect(x, y, self.width, self.width)
        self.img = img

    def move(self,x,y):
        self.x = x
        self.y = y

    def is_touched(self,player: Player) -> bool:
        return self.x < player.x + player.width // 2 < self.x + self.width and self.y < player.y + player.width // 2 < self.y + self.width

class Portal:
    def __init__(self,x,y,id, destination_id, img, img2):
        self.x, self.y = x,y
        self.width = 50
        self.rect = pygame.Rect(x, y, self.width, self.width)
        self.img = img
        self.img2 = img2
        self.id = id
        self.dest_id = destination_id

    def move(self,x,y):
        self.x, self.y = x, y

    def is_touched(self,player: Player):
        return self.x < player.x + player.width // 2 < self.x + self.width and self.y < player.y + player.width // 2 < self.y + self.width

class SubMapPortal:
    def __init__(self, x, y, target_map_index, spawn_pos, img):
        self.x, self.y = x, y
        self.width = 50
        self.rect = pygame.Rect(x, y, self.width, self.width)
        self.target_map_index = target_map_index #Map index in "maps" in level config
        self.spawn_pos = spawn_pos # Player spawn point in new map
        self.img = img

    def is_touched(self, player: Player) -> bool:
        return self.x < player.x + player.width // 2 < self.x + self.width and self.y < player.y + player.width // 2 < self.y + self.width

class Trap :
    def __init__(self,x,y,img):
        self.x,self.y = x,y
        self.width = TILE_SIZE
        self.rect = pygame.Rect(x,y,TILE_SIZE,TILE_SIZE)
        self.img = img
    
    def is_touched(self,player: Player) -> bool:
        return self.rect.colliderect(player.rect)

class Key :
    def __init__(self,x,y,id,img):
        self.x,self.y = x,y
        self.width = TILE_SIZE
        self.collected = False
        self.door_id = id
        from .utils import tint_image
        self.img = tint_image(img,KEY_COLORS.get(self.door_id.lower(), (255, 255, 255)))

    def is_touched(self,player: Player) -> bool:
        return self.x < player.x + player.width // 2 < self.x + self.width and self.y < player.y + player.width // 2 < self.y + self.width
    
    def collect(self):
        self.collected = True
    
    def reset(self):
        self.collected = False

class Light :
    def __init__(self,x,y,img):
        self.x,self.y = x,y
        self.width = TILE_SIZE
        self.collected = False
        self.img = img
        self.effect = TORCH_EFFECT
        self.cooldown = 0.0

    def is_touched(self,player: Player) -> bool:
        return self.x < player.x + player.width // 2 < self.x + self.width and self.y < player.y + player.width // 2 < self.y + self.width

    def collect(self):
        self.collected = True
    
    def respawn(self):
        self.collected = False
    
class Heal :
    def __init__(self,x,y,img):
        self.x, self.y = x,y
        self.width = TILE_SIZE
        self.collected = False
        self.img = img
        self.effect = HEAL_EFFECT

    def is_touched(self,player: Player) -> bool:
        return self.x < player.x + player.width // 2 < self.x + self.width and self.y < player.y + player.width // 2 < self.y + self.width

    def collect(self):
        self.collected = True
    
    def respawn(self):
        self.collected = False

class Speed :
    def __init__(self,x,y,img):
        self.x,self.y = x,y
        self.width = TILE_SIZE
        self.collected = False
        self.img = img
        self.effect = SPEED_EFFECT
        self.cooldown = 0.0

    def is_touched(self,player: Player) -> bool:
        return self.x < player.x + player.width // 2 < self.x + self.width and self.y < player.y + player.width // 2 < self.y + self.width

    def collect(self):
        self.collected = True
    
    def respawn(self):
        self.collected = False

# ==================================================================
# UI classes
# ==================================================================

class ButtonUI:
    def __init__(self,x,y,width: int,height: int,img):
        self.centerx = x
        self.centery = y
        self.width = width
        self.height = height
        self.x = self.centerx - self.width/2
        self.y = self.centery - self.height/2
        self.img = img
    
    def move(self,x,y):
        self.centerx = x
        self.centery = y
        self.x = self.centerx - self.width/2
        self.y = self.centery - self.height/2

    def is_pressed(self,x,y) -> bool:
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height

class TextUI:
    def __init__(self,x,y,font,txt,color):
        if txt is None :
            txt = ""
        self.centerx = x
        self.centery = y
        self.font = font
        self.txt = font.render(txt, 3, color)
        self.color = color
        self.pos = self.txt.get_rect(center=(x,y))