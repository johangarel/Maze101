import random
from .settings import NB_LEVELS


class AudioManager:
    """Manages all audio logic: music, sound effects, and volume."""

    def __init__(self, assets, save_data):
        self._assets = assets
        self.music_play = save_data["music"]
        self.music_animation = False
        self.time_display = 2.0
        self.next_walk_sfx = random.choice(["sfx_walk1","sfx_walk2","sfx_walk3","sfx_walk4"])

        # Active music
        self._active: object = assets["menu_music"]
        self.music_vol = save_data["music_vol"]
        self.sfx_vol = save_data["sfx_vol"]

        # Build playlist indexed by level (1-based, index 0 = menu)
        self._playlist = [None] * (NB_LEVELS + 1)
        self._playlist[0] = assets["menu_music"]
        for i in range(1,8):
            self._playlist[i] = assets[f"music_level{i}"]
        self._playlist[42] = assets["music_level42"]

        # Initialize volumes
        volume = self.music_vol if self.music_play else 0.0
        for track in self._playlist:
            if track is not None:
                track.set_volume(volume)

        self._active.play(loops=-1)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def music_for_level(self, level_id: int):
        """Returns the track associated with the level (None if not defined)."""
        if 0 <= level_id < len(self._playlist):
            return self._playlist[level_id]
        return None

    def switch(self, track) -> None:
        """Switch track. Respects the music_play setting."""
        if self._active is not None:
            self._active.stop()
        self._active = track
        if self._active is not None:
            vol = self.music_vol if self.music_play else 0.0
            self._active.set_volume(vol)
            self._active.play(loops=-1)

    def switch_to_menu(self) -> None:
        if self._active is not self._assets["menu_music"]:
            self.switch(self._assets["menu_music"])

    def switch_to_victory(self) -> None:
        self.switch(self._assets["music_victory"])

    def switch_to_level(self, level_id: int) -> None:
        track = self.music_for_level(level_id)
        if track is not None:
            self.switch(track)

    def toggle(self) -> bool:
        """Toggle mute/unmute. Returns the new state."""
        self.music_play = not self.music_play
        volume = self.music_vol if self.music_play else 0.0
        if self._active is not None:
            self._active.set_volume(volume)
        self.time_display = 2.0
        self.music_animation = True
        return self.music_play

    def play_sfx(self, name: str) -> None:
        sfx = self._assets.get(name)
        if sfx is None :
            return
        sfx.set_volume(self.sfx_vol if self.music_play else 0.0)
        sfx.play()

    def update(self, dt: float) -> None:
        """To be called each frame to manage the music icon animation."""
        if self.music_animation:
            self.time_display -= dt
            if self.time_display <= 0:
                self.music_animation = False
                self.time_display = 2.0
    
    def decide_next_walk_sfx(self):
        l = [sound for sound in ["sfx_walk1","sfx_walk2","sfx_walk3","sfx_walk4"] if sound != self.next_walk_sfx]
        self.next_walk_sfx = random.choice(l)
    
    def update_volume(self):
        if self._active is not None:
            self._active.set_volume(self.music_vol if self.music_play else 0.0)
