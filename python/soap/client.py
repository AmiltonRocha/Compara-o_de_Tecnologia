"""Cliente de exemplo SOAP usando zeep (lê o WSDL servido em /?wsdl).

Execute o servidor SOAP e rode (a partir de python/):
    python3 soap/client.py

Observação: o zeep devolve uma lista diretamente quando a resposta tem um único
elemento repetido (ex.: <users><users>...), e um objeto quando há um único registro.
"""

from zeep import Client

WSDL = "http://localhost:8001/?wsdl"


def main() -> None:
    client = Client(WSDL)

    print("== Usuários ==")
    for user in client.service.ListUsers():
        print(user.id, user.name, user.email)

    print("\n== Músicas ==")
    for music in client.service.ListMusics():
        print(music.id, music.title, music.artist, music.durationSeconds)

    print("\n== Playlists da usuária 1 ==")
    for playlist in client.service.ListPlaylistsByUser(userId=1):
        print(playlist.id, playlist.name, playlist.musicIds)

    print("\n== Músicas da playlist 1 ==")
    for music in client.service.ListMusicsByPlaylist(playlistId=1):
        print(music.id, music.title)

    print("\n== Playlists que contêm a música 2 ==")
    for playlist in client.service.ListPlaylistsByMusic(musicId=2):
        print(playlist.id, playlist.name)


if __name__ == "__main__":
    main()
