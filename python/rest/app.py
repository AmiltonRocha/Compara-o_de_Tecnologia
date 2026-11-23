"""Serviço de streaming de músicas - implementação REST (FastAPI).

Contrato: specs/openapi.yaml
Execução (a partir de python/):
    uvicorn rest.app:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from common.store import NotFoundError, ValidationError, store

app = FastAPI(title="Music Streaming Service (REST)", version="1.0.0")


# ----------------------------------------------------------------- modelos
class UserIn(BaseModel):
    name: str
    email: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None


class MusicIn(BaseModel):
    title: str
    artist: str
    durationSeconds: int


class MusicUpdate(BaseModel):
    title: str | None = None
    artist: str | None = None
    durationSeconds: int | None = None


class PlaylistIn(BaseModel):
    name: str
    ownerId: int
    musicIds: list[int] = []


class PlaylistUpdate(BaseModel):
    name: str | None = None
    ownerId: int | None = None
    musicIds: list[int] | None = None


def user_out(u) -> dict:
    return {"id": u.id, "name": u.name, "email": u.email}


def music_out(m) -> dict:
    return {"id": m.id, "title": m.title, "artist": m.artist, "durationSeconds": m.duration_seconds}


def playlist_out(p) -> dict:
    return {"id": p.id, "name": p.name, "ownerId": p.owner_id, "musicIds": list(p.music_ids)}


# ------------------------------------------------------------------- app
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/users")
def list_users():
    return [user_out(u) for u in store.list_users()]


@app.get("/users/{user_id}")
def get_user(user_id: int):
    try:
        return user_out(store.get_user(user_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/users", status_code=201)
def create_user(body: UserIn):
    return user_out(store.create_user(body.name, body.email))


@app.put("/users/{user_id}")
def update_user(user_id: int, body: UserUpdate):
    try:
        return user_out(store.update_user(user_id, body.name, body.email))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    if not store.delete_user(user_id):
        raise HTTPException(status_code=404, detail="usuário não encontrado")


@app.get("/users/{user_id}/playlists")
def playlists_by_user(user_id: int):
    return [playlist_out(p) for p in store.playlists_by_user(user_id)]


@app.get("/musics")
def list_musics():
    return [music_out(m) for m in store.list_musics()]


@app.get("/musics/{music_id}")
def get_music(music_id: int):
    try:
        return music_out(store.get_music(music_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/musics", status_code=201)
def create_music(body: MusicIn):
    return music_out(store.create_music(body.title, body.artist, body.durationSeconds))


@app.put("/musics/{music_id}")
def update_music(music_id: int, body: MusicUpdate):
    try:
        return music_out(
            store.update_music(music_id, body.title, body.artist, body.durationSeconds)
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.delete("/musics/{music_id}", status_code=204)
def delete_music(music_id: int):
    if not store.delete_music(music_id):
        raise HTTPException(status_code=404, detail="música não encontrada")


@app.get("/musics/{music_id}/playlists")
def playlists_by_music(music_id: int):
    return [playlist_out(p) for p in store.playlists_by_music(music_id)]


@app.get("/playlists")
def list_playlists():
    return [playlist_out(p) for p in store.list_playlists()]


@app.get("/playlists/{playlist_id}")
def get_playlist(playlist_id: int):
    try:
        return playlist_out(store.get_playlist(playlist_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/playlists", status_code=201)
def create_playlist(body: PlaylistIn):
    try:
        return playlist_out(store.create_playlist(body.name, body.ownerId, body.musicIds))
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.put("/playlists/{playlist_id}")
def update_playlist(playlist_id: int, body: PlaylistUpdate):
    try:
        return playlist_out(
            store.update_playlist(playlist_id, body.name, body.ownerId, body.musicIds)
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.delete("/playlists/{playlist_id}", status_code=204)
def delete_playlist(playlist_id: int):
    if not store.delete_playlist(playlist_id):
        raise HTTPException(status_code=404, detail="playlist não encontrada")


@app.get("/playlists/{playlist_id}/musics")
def musics_by_playlist(playlist_id: int):
    try:
        return [music_out(m) for m in store.musics_by_playlist(playlist_id)]
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
