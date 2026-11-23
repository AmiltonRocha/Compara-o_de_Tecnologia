"""Cliente de exemplo gRPC. Execute o servidor e rode (a partir de python/):
    python3 grpc_api/client.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import grpc

import music_pb2 as pb2
import music_pb2_grpc as pb2_grpc


def main() -> None:
    with grpc.insecure_channel("localhost:8003") as channel:
        stub = pb2_grpc.MusicServiceStub(channel)

        print("== Usuários ==")
        for user in stub.ListUsers(pb2.Empty()).users:
            print(user.id, user.name, user.email)

        print("\n== Músicas ==")
        for music in stub.ListMusics(pb2.Empty()).musics:
            print(music.id, music.title, music.artist, music.duration_seconds)

        print("\n== Playlists da usuária 1 ==")
        for playlist in stub.ListPlaylistsByUser(pb2.IdRequest(id=1)).playlists:
            print(playlist.id, playlist.name, list(playlist.music_ids))

        print("\n== Músicas da playlist 1 ==")
        for music in stub.ListMusicsByPlaylist(pb2.IdRequest(id=1)).musics:
            print(music.id, music.title)

        print("\n== Playlists que contêm a música 2 ==")
        for playlist in stub.ListPlaylistsByMusic(pb2.IdRequest(id=2)).playlists:
            print(playlist.id, playlist.name)


if __name__ == "__main__":
    main()
