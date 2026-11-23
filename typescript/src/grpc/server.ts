// Serviço de streaming de músicas - implementação gRPC (@grpc/grpc-js).
// Contrato: specs/music.proto (carregado dinamicamente, sem codegen).
// Execução (a partir de typescript/): npm run grpc -> localhost:8003

import path from "node:path";
import { fileURLToPath } from "node:url";

import * as grpc from "@grpc/grpc-js";
import * as protoLoader from "@grpc/proto-loader";

import { NotFoundError, ValidationError, store } from "../common/store.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const PROTO_PATH = path.resolve(here, "../../../specs/music.proto");

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: false,
  longs: Number,
  enums: String,
  defaults: false,
  oneofs: true,
});
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const proto = grpc.loadPackageDefinition(packageDefinition) as any;

function userMsg(u: { id: number; name: string; email: string }) {
  return { id: u.id, name: u.name, email: u.email };
}

function musicMsg(m: {
  id: number;
  title: string;
  artist: string;
  durationSeconds: number;
}) {
  return {
    id: m.id,
    title: m.title,
    artist: m.artist,
    durationSeconds: m.durationSeconds,
  };
}

function playlistMsg(p: {
  id: number;
  name: string;
  ownerId: number;
  musicIds: number[];
}) {
  return {
    id: p.id,
    name: p.name,
    ownerId: p.ownerId,
    musicIds: p.musicIds,
  };
}

function grpcError(code: number, err: unknown) {
  return {
    code,
    message: (err as Error).message,
    details: (err as Error).message,
    metadata: new grpc.Metadata(),
  };
}

const notFound = (err: unknown) => grpcError(grpc.status.NOT_FOUND, err);
const invalid = (err: unknown) => grpcError(grpc.status.INVALID_ARGUMENT, err);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Call = any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Callback = (err: any, value?: unknown) => void;

const implementation = {
  ListUsers: (_call: Call, cb: Callback) =>
    cb(null, { users: store.listUsers().map(userMsg) }),
  GetUser: (call: Call, cb: Callback) => {
    try {
      cb(null, userMsg(store.getUser(call.request.id)));
    } catch (err) {
      cb(notFound(err));
    }
  },
  CreateUser: (call: Call, cb: Callback) =>
    cb(null, userMsg(store.createUser(call.request.name, call.request.email))),
  UpdateUser: (call: Call, cb: Callback) => {
    try {
      cb(null, userMsg(store.updateUser(call.request.id, call.request.name, call.request.email)));
    } catch (err) {
      cb(notFound(err));
    }
  },
  DeleteUser: (call: Call, cb: Callback) =>
    cb(null, { deleted: store.deleteUser(call.request.id) }),

  ListMusics: (_call: Call, cb: Callback) =>
    cb(null, { musics: store.listMusics().map(musicMsg) }),
  GetMusic: (call: Call, cb: Callback) => {
    try {
      cb(null, musicMsg(store.getMusic(call.request.id)));
    } catch (err) {
      cb(notFound(err));
    }
  },
  CreateMusic: (call: Call, cb: Callback) =>
    cb(
      null,
      musicMsg(
        store.createMusic(
          call.request.title,
          call.request.artist,
          call.request.durationSeconds,
        ),
      ),
    ),
  UpdateMusic: (call: Call, cb: Callback) => {
    try {
      cb(
        null,
        musicMsg(
          store.updateMusic(
            call.request.id,
            call.request.title,
            call.request.artist,
            call.request.durationSeconds,
          ),
        ),
      );
    } catch (err) {
      cb(notFound(err));
    }
  },
  DeleteMusic: (call: Call, cb: Callback) =>
    cb(null, { deleted: store.deleteMusic(call.request.id) }),

  ListPlaylists: (_call: Call, cb: Callback) =>
    cb(null, { playlists: store.listPlaylists().map(playlistMsg) }),
  GetPlaylist: (call: Call, cb: Callback) => {
    try {
      cb(null, playlistMsg(store.getPlaylist(call.request.id)));
    } catch (err) {
      cb(notFound(err));
    }
  },
  CreatePlaylist: (call: Call, cb: Callback) => {
    try {
      cb(
        null,
        playlistMsg(
          store.createPlaylist(
            call.request.name,
            call.request.ownerId,
            call.request.musicIds ?? [],
          ),
        ),
      );
    } catch (err) {
      cb(invalid(err));
    }
  },
  UpdatePlaylist: (call: Call, cb: Callback) => {
    try {
      const musicIds =
        call.request.musicIds && call.request.musicIds.length
          ? call.request.musicIds
          : undefined;
      cb(
        null,
        playlistMsg(
          store.updatePlaylist(
            call.request.id,
            call.request.name,
            call.request.ownerId,
            musicIds,
          ),
        ),
      );
    } catch (err) {
      cb(err instanceof NotFoundError ? notFound(err) : invalid(err));
    }
  },
  DeletePlaylist: (call: Call, cb: Callback) =>
    cb(null, { deleted: store.deletePlaylist(call.request.id) }),

  ListPlaylistsByUser: (call: Call, cb: Callback) =>
    cb(null, { playlists: store.playlistsByUser(call.request.id).map(playlistMsg) }),
  ListMusicsByPlaylist: (call: Call, cb: Callback) => {
    try {
      cb(null, { musics: store.musicsByPlaylist(call.request.id).map(musicMsg) });
    } catch (err) {
      cb(notFound(err));
    }
  },
  ListPlaylistsByMusic: (call: Call, cb: Callback) =>
    cb(null, { playlists: store.playlistsByMusic(call.request.id).map(playlistMsg) }),
};

const server = new grpc.Server();
server.addService(proto.music.MusicService.service, implementation);
server.bindAsync("0.0.0.0:8003", grpc.ServerCredentials.createInsecure(), (err) => {
  if (err) throw err;
  console.log("gRPC MusicService ouvindo em 0.0.0.0:8003");
});
