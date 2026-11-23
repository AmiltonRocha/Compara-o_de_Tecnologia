"""Serviço de streaming de músicas - implementação gRPC (grpcio).

Contrato: specs/music.proto
Execução (a partir de python/):
    ./grpc_api/generate.sh
    python3 grpc_api/server.py
"""

from __future__ import annotations

import os
import sys
from concurrent import futures

# Permite importar o pacote "common" (fica em python/) ao rodar como script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc  # noqa: E402

import music_pb2 as pb2  # noqa: E402
import music_pb2_grpc as pb2_grpc  # noqa: E402
from common.store import (  # noqa: E402
    NotFoundError,
    ValidationError,
    store,
)

PORT = 8003


# --------------------------------------------------------------- conversões
def user_msg(u) -> pb2.User:
    return pb2.User(id=u.id, name=u.name, email=u.email)


def music_msg(m) -> pb2.Music:
    return pb2.Music(
        id=m.id, title=m.title, artist=m.artist, duration_seconds=m.duration_seconds
    )


def playlist_msg(p) -> pb2.Playlist:
    return pb2.Playlist(
        id=p.id, name=p.name, owner_id=p.owner_id, music_ids=list(p.music_ids)
    )


def abort_not_found(context, exc: Exception):
    context.abort(grpc.StatusCode.NOT_FOUND, str(exc))


def abort_invalid(context, exc: Exception):
    context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))


class MusicService(pb2_grpc.MusicServiceServicer):
    # -------------------------------------------------------------- usuários
    def ListUsers(self, request, context):
        return pb2.UserList(users=[user_msg(u) for u in store.list_users()])

    def GetUser(self, request, context):
        try:
            return user_msg(store.get_user(request.id))
        except NotFoundError as exc:
            abort_not_found(context, exc)

    def CreateUser(self, request, context):
        return user_msg(store.create_user(request.name, request.email))

    def UpdateUser(self, request, context):
        try:
            return user_msg(
                store.update_user(
                    request.id,
                    request.name if request.HasField("name") else None,
                    request.email if request.HasField("email") else None,
                )
            )
        except NotFoundError as exc:
            abort_not_found(context, exc)

    def DeleteUser(self, request, context):
        return pb2.DeleteResponse(deleted=store.delete_user(request.id))

    # -------------------------------------------------------------- músicas
    def ListMusics(self, request, context):
        return pb2.MusicList(musics=[music_msg(m) for m in store.list_musics()])

    def GetMusic(self, request, context):
        try:
            return music_msg(store.get_music(request.id))
        except NotFoundError as exc:
            abort_not_found(context, exc)

    def CreateMusic(self, request, context):
        return music_msg(
            store.create_music(request.title, request.artist, request.duration_seconds)
        )

    def UpdateMusic(self, request, context):
        try:
            return music_msg(
                store.update_music(
                    request.id,
                    request.title if request.HasField("title") else None,
                    request.artist if request.HasField("artist") else None,
                    request.duration_seconds
                    if request.HasField("duration_seconds")
                    else None,
                )
            )
        except NotFoundError as exc:
            abort_not_found(context, exc)

    def DeleteMusic(self, request, context):
        return pb2.DeleteResponse(deleted=store.delete_music(request.id))

    # ------------------------------------------------------------- playlists
    def ListPlaylists(self, request, context):
        return pb2.PlaylistList(
            playlists=[playlist_msg(p) for p in store.list_playlists()]
        )

    def GetPlaylist(self, request, context):
        try:
            return playlist_msg(store.get_playlist(request.id))
        except NotFoundError as exc:
            abort_not_found(context, exc)

    def CreatePlaylist(self, request, context):
        try:
            return playlist_msg(
                store.create_playlist(
                    request.name, request.owner_id, list(request.music_ids)
                )
            )
        except ValidationError as exc:
            abort_invalid(context, exc)

    def UpdatePlaylist(self, request, context):
        try:
            return playlist_msg(
                store.update_playlist(
                    request.id,
                    request.name if request.HasField("name") else None,
                    request.owner_id if request.HasField("owner_id") else None,
                    # campo repeated não tem presença em proto3: lista vazia = não alterar
                    list(request.music_ids) if request.music_ids else None,
                )
            )
        except NotFoundError as exc:
            abort_not_found(context, exc)
        except ValidationError as exc:
            abort_invalid(context, exc)

    def DeletePlaylist(self, request, context):
        return pb2.DeleteResponse(deleted=store.delete_playlist(request.id))

    # --------------------------------------------------- consultas relacionais
    def ListPlaylistsByUser(self, request, context):
        return pb2.PlaylistList(
            playlists=[playlist_msg(p) for p in store.playlists_by_user(request.id)]
        )

    def ListMusicsByPlaylist(self, request, context):
        try:
            return pb2.MusicList(
                musics=[music_msg(m) for m in store.musics_by_playlist(request.id)]
            )
        except NotFoundError as exc:
            abort_not_found(context, exc)

    def ListPlaylistsByMusic(self, request, context):
        return pb2.PlaylistList(
            playlists=[playlist_msg(p) for p in store.playlists_by_music(request.id)]
        )


def serve() -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_MusicServiceServicer_to_server(MusicService(), server)
    server.add_insecure_port(f"[::]:{PORT}")
    server.start()
    print(f"gRPC MusicService ouvindo em 0.0.0.0:{PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
