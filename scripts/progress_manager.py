import pygame
import json
import os
from .utils import get_path
from .settings import DEFAULT_MUSIC_VOL, DEFAULT_SFX_VOL, FPS

SAVE_FILE = "save.json"

def _default_save() -> dict:
    return {
        "music": True, 
        "total_stars": 0, 
        "levels": {},
        "music_vol": DEFAULT_MUSIC_VOL,
        "sfx_vol": DEFAULT_SFX_VOL,
        "fps": FPS,
        "keys": {
            "up": pygame.K_z,
            "down": pygame.K_s,
            "left": pygame.K_q,
            "right": pygame.K_d,
            "reset": pygame.K_r,
            "music": pygame.K_e,
            "menu": pygame.K_ESCAPE
        }
    }


def load_game() -> dict:
    path = get_path(SAVE_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            # Corrupted file → start from scratch
            return _default_save()
    return _default_save()


def save_game(data: dict) -> None:
    path = get_path(SAVE_FILE)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


class ProgressManager:
    """
    Manages player progression: stars, best times, and music.
    """

    def __init__(self, nb_levels: int):
        self._nb_levels = nb_levels
        self._data = load_game()

        # In-memory caches
        self.nb_stars: int = self._data["total_stars"]
        self.music_on: bool = self._data["music"]
        self.music_vol : float = self._data["music_vol"]
        self.sfx_vol : float = self._data["sfx_vol"]
        self.keys: dict = self._data.get("keys", _default_save()["keys"])

        self.level_time: list = [None] * nb_levels
        self.reward_collected: list = [False] * nb_levels

        for level_str, info in self._data["levels"].items():
            idx = int(level_str) - 1
            if 0 <= idx < nb_levels:
                self.level_time[idx] = info["best_time"]
                self.reward_collected[idx] = True

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def best_time_display(self, maze_id: int) -> str:
        t = self.level_time[maze_id - 1]
        return str(t) if t is not None else "--.--"

    def is_completed(self, maze_id: int) -> bool:
        return self.reward_collected[maze_id - 1]

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    def record_victory(self, maze_id: int, stars_earned: int, time_spent: float) -> bool:
        """
        Records a victory.

        - Adds earned stars to total.
        - Updates best time if beaten.
        - Returns True if it's a new record.
        """

        idx = maze_id - 1
        new_record = False

        # Stars: only add if level has not been completed yet
        if not self.reward_collected[idx]:
            self.reward_collected[idx] = True
            self.nb_stars += stars_earned
            self._data["total_stars"] = self.nb_stars

        # Best time
        prev = self.level_time[idx]
        if prev is None or time_spent < prev:
            self.level_time[idx] = time_spent
            if prev is None:
                new_record = 1
            else :
                new_record = 2

        # Persistence
        key = str(maze_id)
        if key not in self._data["levels"]:
            self._data["levels"][key] = {}
        self._data["levels"][key]["best_time"] = self.level_time[idx]

        save_game(self._data)
        return new_record

    def save_music_pref(self, music_on: bool):
        self.music_on = music_on
        self._data["music"] = music_on
        save_game(self._data)
    
    def save_settings(self, new_keys: dict, fps, music_vol, sfx_vol):
        self.keys = new_keys
        self._data["keys"] = new_keys
        self._data["fps"] = fps
        self._data["music_vol"] = music_vol
        self._data["sfx_vol"] = sfx_vol
        save_game(self._data)
