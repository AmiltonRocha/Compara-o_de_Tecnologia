// Serviço de streaming de músicas - implementação GraphQL (GraphQL Yoga).
// Contrato: specs/schema.graphql
// Execução (a partir de typescript/): npm run graphql -> http://localhost:8002/graphql

import { readFileSync } from "node:fs";
import { createServer } from "node:http";

import { createSchema, createYoga } from "graphql-yoga";

import { NotFoundError, ValidationError, store } from "../common/store.js";

const typeDefs = readFileSync(
  new URL("../../../specs/schema.graphql", import.meta.url),
  "utf8",
);

const resolvers = {
  Query: {
    users: () => store.listUsers(),
    user: (_: unknown, args: { id: number }) => {
      try {
        return store.getUser(args.id);
      } catch (err) {
        if (err instanceof NotFoundError) return null;
        throw err;
      }
    },
    musics: () => store.listMusics(),
    music: (_: unknown, args: { id: number }) => {
      try {
        return store.getMusic(args.id);
      } catch (err) {
        if (err instanceof NotFoundError) return null;
        throw err;
      }
    },
    playlists: () => store.listPlaylists(),
    playlist: (_: unknown, args: { id: number }) => {
      try {
        return store.getPlaylist(args.id);
      } catch (err) {
        if (err instanceof NotFoundError) return null;
        throw err;
      }
    },
    playlistsByUser: (_: unknown, args: { userId: number }) =>
      store.playlistsByUser(args.userId),
    musicsByPlaylist: (_: unknown, args: { playlistId: number }) => {
      try {
        return store.musicsByPlaylist(args.playlistId);
      } catch (err) {
        if (err instanceof NotFoundError) return [];
        throw err;
      }
    },
    playlistsByMusic: (_: unknown, args: { musicId: number }) =>
      store.playlistsByMusic(args.musicId),
  },
  Mutation: {
    createUser: (_: unknown, { input }: { input: { name: string; email: string } }) =>
      store.createUser(input.name, input.email),
    updateUser: (
      _: unknown,
      { id, input }: { id: number; input: { name?: string; email?: string } },
    ) => {
      try {
        return store.updateUser(id, input.name, input.email);
      } catch (err) {
        if (err instanceof NotFoundError) return null;
        throw err;
      }
    },
    deleteUser: (_: unknown, { id }: { id: number }) => store.deleteUser(id),
    createMusic: (
      _: unknown,
      { input }: { input: { title: string; artist: string; durationSeconds: number } },
    ) => store.createMusic(input.title, input.artist, input.durationSeconds),
    updateMusic: (
      _: unknown,
      {
        id,
        input,
      }: {
        id: number;
        input: { title?: string; artist?: string; durationSeconds?: number };
      },
    ) => {
      try {
        return store.updateMusic(id, input.title, input.artist, input.durationSeconds);
      } catch (err) {
        if (err instanceof NotFoundError) return null;
        throw err;
      }
    },
    deleteMusic: (_: unknown, { id }: { id: number }) => store.deleteMusic(id),
    createPlaylist: (
      _: unknown,
      { input }: { input: { name: string; ownerId: number; musicIds?: number[] } },
    ) => {
      try {
        return store.createPlaylist(input.name, input.ownerId, input.musicIds ?? []);
      } catch (err) {
        if (err instanceof ValidationError) throw new Error(err.message);
        throw err;
      }
    },
    updatePlaylist: (
      _: unknown,
      {
        id,
        input,
      }: {
        id: number;
        input: { name?: string; ownerId?: number; musicIds?: number[] };
      },
    ) => {
      try {
        return store.updatePlaylist(id, input.name, input.ownerId, input.musicIds);
      } catch (err) {
        if (err instanceof NotFoundError) return null;
        if (err instanceof ValidationError) throw new Error(err.message);
        throw err;
      }
    },
    deletePlaylist: (_: unknown, { id }: { id: number }) => store.deletePlaylist(id),
  },
  User: {
    playlists: (parent: { id: number }) => store.playlistsByUser(parent.id),
  },
  Music: {
    playlists: (parent: { id: number }) => store.playlistsByMusic(parent.id),
  },
  Playlist: {
    owner: (parent: { ownerId: number }) => store.getUser(parent.ownerId),
    musics: (parent: { id: number }) => store.musicsByPlaylist(parent.id),
  },
};

const schema = createSchema({ typeDefs, resolvers });
const yoga = createYoga({ schema, graphqlEndpoint: "/graphql" });

createServer(yoga).listen(8002, "0.0.0.0", () => {
  console.log("GraphQL MusicService ouvindo em http://0.0.0.0:8002/graphql");
});
