"""Modelo de domínio e armazenamento em memória compartilhado pelos 4 serviços Python.

Cada processo de servidor carrega a mesma seed (ver specs/data-model.md), de modo que
SOAP, REST, GraphQL e gRPC exponham exatamente os mesmos dados e operações.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock


class NotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


@dataclass
class User:
    id: int
    name: str
    email: str


@dataclass
class Music:
    id: int
    title: str
    artist: str
    duration_seconds: int


@dataclass
class Playlist:
    id: int
    name: str
    owner_id: int
    music_ids: list[int] = field(default_factory=list)


class Store:
    def __init__(self) -> None:
        self._lock = RLock()
        self.users: dict[int, User] = {}
        self.musics: dict[int, Music] = {}
        self.playlists: dict[int, Playlist] = {}
        self._next_user = 1
        self._next_music = 1
        self._next_playlist = 1
        self._seed()

    # ------------------------------------------------------------------ seed
    def _seed(self) -> None:
        for name, email in [
            ("Ana Silva", "ana@example.com"),
            ("Bruno Costa", "bruno@example.com"),
            ("Carla Dias", "carla@example.com"),
        ]:
            self.create_user(name, email)

        for title, artist, duration in [
            ("Song One", "Artist A", 210),
            ("Song Two", "Artist B", 185),
            ("Song Three", "Artist A", 240),
            ("Song Four", "Artist C", 199),
            ("Song Five", "Artist B", 300),
        ]:
            self.create_music(title, artist, duration)

        self.create_playlist("Favoritas da Ana", 1, [1, 2, 3])
        self.create_playlist("Treino do Bruno", 2, [2, 4])
        self.create_playlist("Chill da Carla", 3, [1, 5])
        self.create_playlist("Roadtrip da Ana", 1, [3, 5])

    # --------------------------------------------------------------- usuários
    def list_users(self) -> list[User]:
        with self._lock:
            return sorted(self.users.values(), key=lambda u: u.id)

    def get_user(self, user_id: int) -> User:
        with self._lock:
            try:
                return self.users[user_id]
            except KeyError:
                raise NotFoundError(f"usuário {user_id} não encontrado")

    def create_user(self, name: str, email: str) -> User:
        with self._lock:
            user = User(self._next_user, name, email)
            self.users[user.id] = user
            self._next_user += 1
            return user

    def update_user(self, user_id: int, name: str | None = None, email: str | None = None) -> User:
        with self._lock:
            user = self.get_user(user_id)
            if name is not None:
                user.name = name
            if email is not None:
                user.email = email
            return user

    def delete_user(self, user_id: int) -> bool:
        with self._lock:
            if user_id not in self.users:
                return False
            del self.users[user_id]
            for playlist in list(self.playlists.values()):
                if playlist.owner_id == user_id:
                    del self.playlists[playlist.id]
            return True

    # --------------------------------------------------------------- músicas
    def list_musics(self) -> list[Music]:
        with self._lock:
            return sorted(self.musics.values(), key=lambda m: m.id)

    def get_music(self, music_id: int) -> Music:
        with self._lock:
            try:
                return self.musics[music_id]
            except KeyError:
                raise NotFoundError(f"música {music_id} não encontrada")

    def create_music(self, title: str, artist: str, duration_seconds: int) -> Music:
        with self._lock:
            music = Music(self._next_music, title, artist, duration_seconds)
            self.musics[music.id] = music
            self._next_music += 1
            return music

    def update_music(
        self,
        music_id: int,
        title: str | None = None,
        artist: str | None = None,
        duration_seconds: int | None = None,
    ) -> Music:
        with self._lock:
            music = self.get_music(music_id)
            if title is not None:
                music.title = title
            if artist is not None:
                music.artist = artist
            if duration_seconds is not None:
                music.duration_seconds = duration_seconds
            return music

    def delete_music(self, music_id: int) -> bool:
        with self._lock:
            if music_id not in self.musics:
                return False
            del self.musics[music_id]
            for playlist in self.playlists.values():
                if music_id in playlist.music_ids:
                    playlist.music_ids.remove(music_id)
            return True

    # -------------------------------------------------------------- playlists
    def list_playlists(self) -> list[Playlist]:
        with self._lock:
            return sorted(self.playlists.values(), key=lambda p: p.id)

    def get_playlist(self, playlist_id: int) -> Playlist:
        with self._lock:
            try:
                return self.playlists[playlist_id]
            except KeyError:
                raise NotFoundError(f"playlist {playlist_id} não encontrada")

    def _validate_refs(self, owner_id: int, music_ids: list[int]) -> None:
        if owner_id not in self.users:
            raise ValidationError(f"usuário {owner_id} não existe")
        for music_id in music_ids:
            if music_id not in self.musics:
                raise ValidationError(f"música {music_id} não existe")

    def create_playlist(self, name: str, owner_id: int, music_ids: list[int] | None = None) -> Playlist:
        with self._lock:
            music_ids = list(music_ids or [])
            self._validate_refs(owner_id, music_ids)
            playlist = Playlist(self._next_playlist, name, owner_id, music_ids)
            self.playlists[playlist.id] = playlist
            self._next_playlist += 1
            return playlist

    def update_playlist(
        self,
        playlist_id: int,
        name: str | None = None,
        owner_id: int | None = None,
        music_ids: list[int] | None = None,
    ) -> Playlist:
        with self._lock:
            playlist = self.get_playlist(playlist_id)
            new_owner = playlist.owner_id if owner_id is None else owner_id
            new_musics = playlist.music_ids if music_ids is None else list(music_ids)
            self._validate_refs(new_owner, new_musics)
            if name is not None:
                playlist.name = name
            playlist.owner_id = new_owner
            playlist.music_ids = new_musics
            return playlist

    def delete_playlist(self, playlist_id: int) -> bool:
        with self._lock:
            if playlist_id not in self.playlists:
                return False
            del self.playlists[playlist_id]
            return True

    # ---------------------------------------------------- consultas relacionais
    def playlists_by_user(self, user_id: int) -> list[Playlist]:
        with self._lock:
            return [p for p in self.list_playlists() if p.owner_id == user_id]

    def musics_by_playlist(self, playlist_id: int) -> list[Music]:
        with self._lock:
            playlist = self.get_playlist(playlist_id)
            return [self.musics[mid] for mid in playlist.music_ids if mid in self.musics]

    def playlists_by_music(self, music_id: int) -> list[Playlist]:
        with self._lock:
            return [p for p in self.list_playlists() if music_id in p.music_ids]


store = Store()
