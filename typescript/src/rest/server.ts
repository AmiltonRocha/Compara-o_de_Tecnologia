// Serviço de streaming de músicas - implementação REST (Express).
// Contrato: specs/openapi.yaml
// Execução (a partir de typescript/): npm run rest   -> http://localhost:8000

import express from "express";

import { NotFoundError, ValidationError, store } from "../common/store.js";

const app = express();
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

// usuários
app.get("/users", (_req, res) => {
  res.json(store.listUsers());
});

app.get("/users/:id", (req, res) => {
  res.json(store.getUser(Number(req.params.id)));
});

app.post("/users", (req, res) => {
  const { name, email } = req.body;
  res.status(201).json(store.createUser(name, email));
});

app.put("/users/:id", (req, res) => {
  const { name, email } = req.body;
  res.json(store.updateUser(Number(req.params.id), name, email));
});

app.delete("/users/:id", (req, res) => {
  if (!store.deleteUser(Number(req.params.id))) {
    throw new NotFoundError("usuário não encontrado");
  }
  res.status(204).end();
});

app.get("/users/:id/playlists", (req, res) => {
  res.json(store.playlistsByUser(Number(req.params.id)));
});

// músicas
app.get("/musics", (_req, res) => {
  res.json(store.listMusics());
});

app.get("/musics/:id", (req, res) => {
  res.json(store.getMusic(Number(req.params.id)));
});

app.post("/musics", (req, res) => {
  const { title, artist, durationSeconds } = req.body;
  res.status(201).json(store.createMusic(title, artist, durationSeconds));
});

app.put("/musics/:id", (req, res) => {
  const { title, artist, durationSeconds } = req.body;
  res.json(store.updateMusic(Number(req.params.id), title, artist, durationSeconds));
});

app.delete("/musics/:id", (req, res) => {
  if (!store.deleteMusic(Number(req.params.id))) {
    throw new NotFoundError("música não encontrada");
  }
  res.status(204).end();
});

app.get("/musics/:id/playlists", (req, res) => {
  res.json(store.playlistsByMusic(Number(req.params.id)));
});

// playlists
app.get("/playlists", (_req, res) => {
  res.json(store.listPlaylists());
});

app.get("/playlists/:id", (req, res) => {
  res.json(store.getPlaylist(Number(req.params.id)));
});

app.post("/playlists", (req, res) => {
  const { name, ownerId, musicIds } = req.body;
  res.status(201).json(store.createPlaylist(name, ownerId, musicIds));
});

app.put("/playlists/:id", (req, res) => {
  const { name, ownerId, musicIds } = req.body;
  res.json(store.updatePlaylist(Number(req.params.id), name, ownerId, musicIds));
});

app.delete("/playlists/:id", (req, res) => {
  if (!store.deletePlaylist(Number(req.params.id))) {
    throw new NotFoundError("playlist não encontrada");
  }
  res.status(204).end();
});

app.get("/playlists/:id/musics", (req, res) => {
  res.json(store.musicsByPlaylist(Number(req.params.id)));
});

app.use((err: Error, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  if (err instanceof NotFoundError) {
    res.status(404).json({ detail: err.message });
  } else if (err instanceof ValidationError) {
    res.status(400).json({ detail: err.message });
  } else {
    res.status(500).json({ detail: err.message });
  }
});

app.listen(8000, "0.0.0.0", () => {
  console.log("REST MusicService ouvindo em http://0.0.0.0:8000");
});
