from .entities import Key, Door, Enemy, Shadow
from .maze import Maze
from .utils import load_map, generate_custom_maze, load_level_meta, load_levels_config
from .settings import (
    NB_LEVELS, TILE_SIZE, VISION_RADIUS, ENEMY_SPEED_PATROL, ENEMY_SPEED_CHASE, ENEMY_DETECTION_RADIUS
)


class LevelManager:
    """Loads, resets, and exposes data for each level."""

    def __init__(self, player, level_configs: dict = None):
        self._player = player
        # Load configs from central file or use provided ones for backwards compatibility
        self.level_configs = level_configs if level_configs else load_levels_config()
        
        # Data per level (0-based indexed lists, level N → index N-1)
        self.wall_list         = [[] for _ in range(NB_LEVELS)]
        self.special_objs_list = [[] for _ in range(NB_LEVELS)]
        self.level_map_list    = [None for _ in range(NB_LEVELS)]
        self.enemy_list        = [[] for _ in range(NB_LEVELS)]

        self.vision_radius = VISION_RADIUS
        self.shadow = None  # Shadow entity
        self.shadow_enabled = False  # Whether shadow is enabled for current level

    # ------------------------------------------------------------------
    # Current access
    # ------------------------------------------------------------------

    def walls(self, maze_id: int) -> list:
        return self.wall_list[maze_id - 1]

    def special_objs(self, maze_id: int) -> list:
        return self.special_objs_list[maze_id - 1]

    def has_fow(self, maze_id: int) -> bool:
        cfg = self.level_configs.get(maze_id)
        return bool(cfg and cfg.get("fow"))
    
    def has_shadow(self, maze_id: int) -> bool:
        """Check if shadow system is enabled for this level"""
        meta_filename = f"level{maze_id}_meta.json"
        meta_data = load_level_meta(meta_filename)
        return bool(meta_data.get("shadow", False))
    
    def enemies(self, maze_id):
        return self.enemy_list[maze_id - 1]

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_sub_map(self, maze_id: int, map_index: int, game, first_map: bool) -> None:
        """Load a sub-map and update internal lists."""
        config = self.level_configs[maze_id]
        layout, spawn_override = self._build_layout(maze_id, map_index)
        
        # Load submap routes from meta JSON
        meta_filename = f"level{maze_id}_meta.json"
        meta_data = load_level_meta(meta_filename)
        submap_routes = meta_data.get("submap_routes", {})

        current_maze = Maze(layout, config["tps"], self._player, game, map_index=map_index, submap_routes=submap_routes)
        self.enemy_list[maze_id - 1] = self._build_enemies(maze_id, map_index, current_maze.enemy_spawns, game)
        spawn = spawn_override or current_maze.spawn_point

        self.level_map_list[maze_id - 1]    = layout
        self.wall_list[maze_id - 1]         = current_maze.walls
        self.special_objs_list[maze_id - 1] = current_maze.special_objs
        self.vision_radius = VISION_RADIUS

        if first_map :
            self._player.move_spawn(spawn[0], spawn[1])
            self._player.respawn()
        return layout  # returned so Game can recalculate dimensions

    def load_level(self, maze_id: int, game) -> None:
        """Load the complete level (sub-map 0) and mark the level as loaded."""
        config = self.level_configs[maze_id]
        layout, spawn_override = self._build_layout(maze_id, 0)
        
        # Load submap routes from meta JSON
        meta_filename = f"level{maze_id}_meta.json"
        meta_data = load_level_meta(meta_filename)
        submap_routes = meta_data.get("submap_routes", {})

        current_maze = Maze(layout, config["tps"], self._player, game, map_index=0, submap_routes=submap_routes)
        self.enemy_list[maze_id - 1] = self._build_enemies(maze_id, 0, current_maze.enemy_spawns, game)
        spawn = spawn_override or current_maze.spawn_point

        self.level_map_list[maze_id - 1]    = layout
        self.wall_list[maze_id - 1]         = current_maze.walls
        self.special_objs_list[maze_id - 1] = current_maze.special_objs
        config["loaded"] = True

        self._player.move_spawn(spawn[0], spawn[1])
        self._player.respawn()
        self.vision_radius = VISION_RADIUS

        return layout

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset_objects(self, maze_id: int) -> None:
        """Reset keys and doors of the level (player death)."""
        for obj in self.special_objs_list[maze_id - 1]:
            if isinstance(obj, (Key, Door)):
                obj.reset()

    def reset_vision(self) -> None:
        self.vision_radius = VISION_RADIUS

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_layout(self, maze_id: int, map_index: int) -> list:
        """Generates or reads the grid according to the level."""
        # Level 3: procedural generation
        if maze_id == 3:
            return self._generate_level3(map_index)

        config = self.level_configs[maze_id]
        return load_map(config["file"][map_index]), None

    def _generate_level3(self, map_index: int) -> list:
        spawn_override = (int(TILE_SIZE / 4), TILE_SIZE)

        if map_index == 0:
            layout = generate_custom_maze(31, 21, ("P", 0, 1), ("S", 30, 19))

        elif map_index == 1:
            layout = generate_custom_maze(31, 21, (" ", 0, 1), ("S", 30, 1))
            # Add a second 'S' exit at the bottom-right corner
            row_list       = list(layout[19])
            row_list[30]   = "S"
            layout[19]     = "".join(row_list)

        else:  # map_index == 2
            layout = generate_custom_maze(31, 21, (" ", 0, 1), ("!", 30, 19))

        return layout, spawn_override

    def _build_enemies(self, maze_id, map_index, spawns, game):
        enemies = []
        
        # Load enemy data from meta JSON file
        meta_filename = f"level{maze_id}_meta.json"
        meta_data = load_level_meta(meta_filename)
        meta_enemies = meta_data.get("enemies", [])
        
        # Build enemies from spawns combined with patrol data from meta
        for i, (sx, sy) in enumerate(spawns):
            # Get patrol data from JSON if available
            patrol_path = [(sx, sy)]  # Default: stay at spawn
            
            if i < len(meta_enemies):
                enemy_config = meta_enemies[i]
                if "patrol" in enemy_config:
                    # Convert grid coordinates to pixels
                    patrol_grid = enemy_config["patrol"]
                    patrol_path = [
                        (waypoint[0] * TILE_SIZE, waypoint[1] * TILE_SIZE)
                        for waypoint in patrol_grid
                    ]
            
            enemies.append(Enemy(
                sx, sy, patrol_path,
                ENEMY_SPEED_PATROL, ENEMY_SPEED_CHASE, ENEMY_DETECTION_RADIUS,
                game.assets["enemy"], map_index
            ))
        
        return enemies

