// @ts-nocheck
// Serviço de streaming de músicas - implementação SOAP 1.1 (node-soap + Express).
// Contrato: specs/music-service.wsdl (servido em GET /?wsdl)
// Execução (a partir de typescript/): npm run soap -> http://localhost:8001

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import express from "express";
import soap from "soap";

import { NotFoundError, ValidationError, store } from "../common/store.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const WSDL = path.resolve(here, "../../../specs/music-service.wsdl");
const wsdlXml = readFileSync(WSDL, "utf8");

function optional(value) {
  return value === undefined || value === null || value === "" ? undefined : value;
}

const service = {
  MusicService: {
    MusicServicePort: {
      // usuários
      ListUsers: async () => ({ users: store.listUsers() }),
      GetUser: async (args) => ({ user: store.getUser(Number(args.id)) }),
      CreateUser: async (args) => ({
        user: store.createUser(args.name, args.email),
      }),
      UpdateUser: async (args) => ({
        user: store.updateUser(
          Number(args.id),
          optional(args.name),
          optional(args.email),
        ),
      }),
      DeleteUser: async (args) => ({
        deleted: store.deleteUser(Number(args.id)),
      }),

      // músicas
      ListMusics: async () => ({ musics: store.listMusics() }),
      GetMusic: async (args) => ({ music: store.getMusic(Number(args.id)) }),
      CreateMusic: async (args) => ({
        music: store.createMusic(
          args.title,
          args.artist,
          Number(args.durationSeconds),
        ),
      }),
      UpdateMusic: async (args) => ({
        music: store.updateMusic(
          Number(args.id),
          optional(args.title),
          optional(args.artist),
          optional(args.durationSeconds) === undefined
            ? undefined
            : Number(args.durationSeconds),
        ),
      }),
      DeleteMusic: async (args) => ({
        deleted: store.deleteMusic(Number(args.id)),
      }),

      // playlists
      ListPlaylists: async () => ({ playlists: store.listPlaylists() }),
      GetPlaylist: async (args) => ({
        playlist: store.getPlaylist(Number(args.id)),
      }),
      CreatePlaylist: async (args) => {
        const musicIds = [].concat(args.musicIds ?? []).map(Number);
        return {
          playlist: store.createPlaylist(
            args.name,
            Number(args.ownerId),
            musicIds,
          ),
        };
      },
      UpdatePlaylist: async (args) => {
        let musicIds;
        if (args.musicIds !== undefined) {
          musicIds = [].concat(args.musicIds).map(Number);
        }
        return {
          playlist: store.updatePlaylist(
            Number(args.id),
            optional(args.name),
            optional(args.ownerId) === undefined
              ? undefined
              : Number(args.ownerId),
            musicIds,
          ),
        };
      },
      DeletePlaylist: async (args) => ({
        deleted: store.deletePlaylist(Number(args.id)),
      }),

      // consultas relacionais
      ListPlaylistsByUser: async (args) => ({
        playlists: store.playlistsByUser(Number(args.userId)),
      }),
      ListMusicsByPlaylist: async (args) => ({
        musics: store.musicsByPlaylist(Number(args.playlistId)),
      }),
      ListPlaylistsByMusic: async (args) => ({
        playlists: store.playlistsByMusic(Number(args.musicId)),
      }),
    },
  },
};

const app = express();
app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

soap.listen(app, "/", service, wsdlXml, () => {
  console.log("SOAP MusicService ouvindo em http://0.0.0.0:8001 (WSDL em /?wsdl)");
});

app.listen(8001, "0.0.0.0");
