import pygame
import random
import os
import sys
import json
import heapq
from .entities import Wall


def get_path(*relative_path):
    if getattr(sys, 'frozen', False):
        # .exe
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        # coding
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(BASE_DIR, *relative_path)

def load_map(filename) -> list :
    path = get_path("levels",filename)
    level_map = []
    with open(path, "r") as file:
        for line in file:
            level_map.append(line.rstrip('\n'))
    return level_map

def load_level_meta(filename) -> dict:
    path = get_path("levels", filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"enemies": []}

def load_levels_config() -> dict:
    """Load the central levels configuration file and merge with meta files."""
    path = get_path("levels", "levels_config.json")
    if not os.path.exists(path):
        return {}
    
    with open(path, "r") as f:
        levels_config = json.load(f)
    
    # Merge each level with its meta file
    result = {}
    for level_id, config in levels_config.items():
        meta_filename = config.get("meta", f"level{level_id}_meta.json")
        meta_data = load_level_meta(meta_filename)
        
        # Combine config and meta
        color = meta_data.get("color", [255, 255, 255])
        if isinstance(color, list):
            color = tuple(color)
        
        result[int(level_id)] = {
            "file": config.get("files", []),
            "tps": meta_data.get("tps", []),
            "fow": meta_data.get("fow", False),
            "submap_fow": meta_data.get("submap_fow", {}),
            "name": meta_data.get("name"),
            "color": color,
            "reward": meta_data.get("reward", 0),
            "loaded": False
        }
    
    return result

def astar(layout: list, start: tuple, end: tuple, tile_size: int) -> list:
    """
    A* pathfinding on the level grid.
 
    start / end : pixel coords (x, y) — converted to grid (col, row) internally.
    Returns an ordered list of pixel (x, y) waypoints to follow, or [] if no
    path exists.
 
    Walkable cells: anything that is not a wall ('W') or a door (uppercase letter, excluding 'E' for enemy spawn)
    """
    def to_grid(px, py):
        return (int(px // tile_size), int(py // tile_size))

    def to_pixel(col, row):
        return (col * tile_size, row * tile_size)

    def is_walkable(col, row):
        if row < 0 or row >= len(layout):
            return False
        if col < 0 or col >= len(layout[row]):
            return False
        ch = layout[row][col]
        # 'E' (enemy spawn) is walkable, but other uppercase letters (doors) are not
        return not (ch == 'W' or (ch.isupper() and ch != 'E'))

    sc, sr = to_grid(*start)
    ec, er = to_grid(*end)

    if not is_walkable(ec, er):
        best = None
        best_dist = float("inf")
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                nc, nr = ec + dc, er + dr
                if is_walkable(nc, nr) and (nc, nr) != (sc, sr):
                    px = nc * tile_size - end[0]
                    py = nr * tile_size - end[1]
                    d = px * px + py * py
                    if d < best_dist:
                        best_dist = d
                        best = (nc, nr)
        if best is None:
            return []
        ec, er = best
 
    # heap entries: (f, g, col, row, path)
    open_set = [(0, 0, sc, sr, [])]
    visited  = set()
 
    while open_set:
        f, g, col, row, path = heapq.heappop(open_set)
        if (col, row) in visited:
            continue
        visited.add((col, row))
        path = path + [(col, row)]
 
        if (col, row) == (ec, er):
            # Skip the first node (already standing there), return pixel coords
            return [to_pixel(c, r) for c, r in path[1:]]
 
        for dc, dr in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nc, nr = col + dc, row + dr
            if (nc, nr) not in visited and is_walkable(nc, nr):
                ng = g + 1
                h  = abs(nc - ec) + abs(nr - er)
                heapq.heappush(open_set, (ng + h, ng, nc, nr, path))
 
    return []  # no path found

def optimise_walls(walls: list) -> list :
    if not walls:
        return []

    # Work on rectangles for optimization
    rects = [w.rect.copy() for w in walls]
    
    # Horizontal fusion
    rects.sort(key=lambda r: (r.y, r.x))
    h_fused = []
    if rects:
        curr = rects[0]
        for next_r in rects[1:]:
            if next_r.y == curr.y and next_r.x == curr.x + curr.width and next_r.height == curr.height:
                curr.width += next_r.width
            else:
                h_fused.append(curr)
                curr = next_r
        h_fused.append(curr)

    # Vertical fusion
    h_fused.sort(key=lambda r: (r.x, r.y))
    v_fused = []
    if h_fused:
        curr = h_fused[0]
        for next_r in h_fused[1:]:
            if next_r.x == curr.x and next_r.y == curr.y + curr.height and next_r.width == curr.width:
                curr.height += next_r.height
            else:
                v_fused.append(curr)
                curr = next_r
        v_fused.append(curr)

    return [Wall(r.x, r.y, r.width, r.height) for r in v_fused]

def invert_color(rvb: tuple) -> tuple:
    r, v, b = rvb
    return (255 - r, 255 - v, 255 - b)

def tint_image(surface, color):
    """Returns a copy of the surface tinted with the given color."""
    tinted = surface.copy()
    tinted.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
    return tinted

def generate_custom_maze(width: int, height: int, entry_info: tuple, exit_info: tuple) -> list:
    """
    entry_info/exit_info : tuple (char, x, y)
    """
    # Create grid
    grid = [['W' for _ in range(width)] for _ in range(height)]

    # Create maze by DFS
    def carve(x, y):
        grid[y][x] = ' '
        directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 < nx < width-1 and 0 < ny < height-1 and grid[ny][nx] == 'W':
                grid[y + dy // 2][x + dx // 2] = ' '
                carve(nx, ny)

    carve(1, 1)

    # Entry placement
    e_char, ex, ey = entry_info
    grid[ey][ex] = e_char
    # Open the maze's entry
    if ex == 0: 
        grid[ey][ex+1] = ' '
    elif ex == width-1: 
        grid[ey][ex-1] = ' '

    # Exit(s) placement(s)
    s_char, sx, sy = exit_info
    grid[sy][sx] = s_char
    # Open the maze's exit
    if sx == 0: 
        grid[sy][sx+1] = ' '
    elif sx == width-1: 
        grid[sy][sx-1] = ' '

    return ["".join(row) for row in grid]