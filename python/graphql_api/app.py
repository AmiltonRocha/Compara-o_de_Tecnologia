"""Serviço de streaming de músicas - implementação GraphQL (Strawberry + FastAPI).

Contrato: specs/schema.graphql
Execução (a partir de python/):
    uvicorn graphql.app:app --host 0.0.0.0 --port 8002
"""

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from common.store import NotFoundError, ValidationError, store


# ------------------------------------------------------------------- tipos
@strawberry.type(name="User")
class User:
    id: int
    name: str
    email: str

    @strawberry.field
    def playlists(self) -> list["Playlist"]:
        return [to_playlist(p) for p in store.playlists_by_user(self.id)]


@strawberry.type(name="Music")
class Music:
    id: int
    title: str
    artist: str
    duration_seconds: int

    @strawberry.field
    def playlists(self) -> list["Playlist"]:
        return [to_playlist(p) for p in store.playlists_by_music(self.id)]


@strawberry.type(name="Playlist")
class Playlist:
    id: int
    name: str
    owner_id: int
    music_ids: list[int]

    @strawberry.field
    def owner(self) -> User:
        return to_user(store.get_user(self.owner_id))

    @strawberry.field
    def musics(self) -> list[Music]:
        return [to_music(m) for m in store.musics_by_playlist(self.id)]


def to_user(u) -> User:
    return User(id=u.id, name=u.name, email=u.email)


def to_music(m) -> Music:
    return Music(id=m.id, title=m.title, artist=m.artist, duration_seconds=m.duration_seconds)


def to_playlist(p) -> Playlist:
    return Playlist(id=p.id, name=p.name, owner_id=p.owner_id, music_ids=list(p.music_ids))


# ------------------------------------------------------------------ inputs
@strawberry.input
class UserInput:
    name: str
    email: str


@strawberry.input
class UserUpdateInput:
    name: str | None = None
    email: str | None = None


@strawberry.input
class MusicInput:
    title: str
    artist: str
    duration_seconds: int


@strawberry.input
class MusicUpdateInput:
    title: str | None = None
    artist: str | None = None
    duration_seconds: int | None = None


@strawberry.input
class PlaylistInput:
    name: str
    owner_id: int
    music_ids: list[int] = strawberry.field(default_factory=list)


@strawberry.input
class PlaylistUpdateInput:
    name: str | None = None
    owner_id: int | None = None
    music_ids: list[int] | None = None


# ----------------------------------------------------------------- queries
@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> list[User]:
        return [to_user(u) for u in store.list_users()]

    @strawberry.field
    def user(self, id: int) -> User | None:
        try:
            return to_user(store.get_user(id))
        except NotFoundError:
            return None

    @strawberry.field
    def musics(self) -> list[Music]:
        return [to_music(m) for m in store.list_musics()]

    @strawberry.field
    def music(self, id: int) -> Music | None:
        try:
            return to_music(store.get_music(id))
        except NotFoundError:
            return None

    @strawberry.field
    def playlists(self) -> list[Playlist]:
        return [to_playlist(p) for p in store.list_playlists()]

    @strawberry.field
    def playlist(self, id: int) -> Playlist | None:
        try:
            return to_playlist(store.get_playlist(id))
        except NotFoundError:
            return None

    @strawberry.field
    def playlists_by_user(self, user_id: int) -> list[Playlist]:
        return [to_playlist(p) for p in store.playlists_by_user(user_id)]

    @strawberry.field
    def musics_by_playlist(self, playlist_id: int) -> list[Music]:
        try:
            return [to_music(m) for m in store.musics_by_playlist(playlist_id)]
        except NotFoundError:
            return []

    @strawberry.field
    def playlists_by_music(self, music_id: int) -> list[Playlist]:
        return [to_playlist(p) for p in store.playlists_by_music(music_id)]


# --------------------------------------------------------------- mutations
@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, input: UserInput) -> User:
        return to_user(store.create_user(input.name, input.email))

    @strawberry.mutation
    def update_user(self, id: int, input: UserUpdateInput) -> User | None:
        try:
            return to_user(store.update_user(id, input.name, input.email))
        except NotFoundError:
            return None

    @strawberry.mutation
    def delete_user(self, id: int) -> bool:
        return store.delete_user(id)

    @strawberry.mutation
    def create_music(self, input: MusicInput) -> Music:
        return to_music(store.create_music(input.title, input.artist, input.duration_seconds))

    @strawberry.mutation
    def update_music(self, id: int, input: MusicUpdateInput) -> Music | None:
        try:
            return to_music(
                store.update_music(id, input.title, input.artist, input.duration_seconds)
            )
        except NotFoundError:
            return None

    @strawberry.mutation
    def delete_music(self, id: int) -> bool:
        return store.delete_music(id)

    @strawberry.mutation
    def create_playlist(self, input: PlaylistInput) -> Playlist:
        try:
            return to_playlist(store.create_playlist(input.name, input.owner_id, input.music_ids))
        except ValidationError as exc:
            raise ValueError(str(exc))

    @strawberry.mutation
    def update_playlist(self, id: int, input: PlaylistUpdateInput) -> Playlist | None:
        try:
            return to_playlist(
                store.update_playlist(id, input.name, input.owner_id, input.music_ids)
            )
        except NotFoundError:
            return None
        except ValidationError as exc:
            raise ValueError(str(exc))

    @strawberry.mutation
    def delete_playlist(self, id: int) -> bool:
        return store.delete_playlist(id)


schema = strawberry.Schema(query=Query, mutation=Mutation)
app = FastAPI(title="Music Streaming Service (GraphQL)", version="1.0.0")
app.include_router(GraphQLRouter(schema), prefix="/graphql")


@app.get("/health")
def health():
    return {"status": "ok"}
