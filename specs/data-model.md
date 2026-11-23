# Modelo de dados e seed compartilhado

Todos os serviços (SOAP, REST, GraphQL e gRPC) usam o mesmo modelo e os mesmos dados iniciais,
para que os testes de carga comparem apenas o mecanismo de invocação.

## Entidades

```
User 1 --- N Playlist N --- N Music
```

- `User(id, name, email)`
- `Music(id, title, artist, durationSeconds)`
- `Playlist(id, name, ownerId, musicIds[])`

## Consultas obrigatórias do enunciado

| Consulta | REST | GraphQL | gRPC | SOAP |
|---|---|---|---|---|
| Listar todos os usuários | `GET /users` | `users` | `ListUsers` | `ListUsers` |
| Listar todas as músicas | `GET /musics` | `musics` | `ListMusics` | `ListMusics` |
| Playlists de um usuário | `GET /users/{id}/playlists` | `playlistsByUser` | `ListPlaylistsByUser` | `ListPlaylistsByUser` |
| Músicas de uma playlist | `GET /playlists/{id}/musics` | `musicsByPlaylist` | `ListMusicsByPlaylist` | `ListMusicsByPlaylist` |
| Playlists que contêm uma música | `GET /musics/{id}/playlists` | `playlistsByMusic` | `ListPlaylistsByMusic` | `ListPlaylistsByMusic` |

## Seed

Usuários:

| id | name | email |
|---|---|---|
| 1 | Ana Silva | ana@example.com |
| 2 | Bruno Costa | bruno@example.com |
| 3 | Carla Dias | carla@example.com |

Músicas:

| id | title | artist | durationSeconds |
|---|---|---|---|
| 1 | Song One | Artist A | 210 |
| 2 | Song Two | Artist B | 185 |
| 3 | Song Three | Artist A | 240 |
| 4 | Song Four | Artist C | 199 |
| 5 | Song Five | Artist B | 300 |

Playlists:

| id | name | ownerId | musicIds |
|---|---|---|---|
| 1 | Favoritas da Ana | 1 | [1, 2, 3] |
| 2 | Treino do Bruno | 2 | [2, 4] |
| 3 | Chill da Carla | 3 | [1, 5] |
| 4 | Roadtrip da Ana | 1 | [3, 5] |
