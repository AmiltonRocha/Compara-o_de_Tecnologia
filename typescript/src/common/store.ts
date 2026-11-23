// Modelo de domínio e armazenamento em memória compartilhado pelos 4 serviços TS.
// Mesma seed de python/common/store.py e specs/data-model.md.

export interface User {
  id: number;
  name: string;
  email: string;
}

export interface Music {
  id: number;
  title: string;
  artist: string;
  durationSeconds: number;
}

export interface Playlist {
  id: number;
  name: string;
  ownerId: number;
  musicIds: number[];
}

export class NotFoundError extends Error {}
export class ValidationError extends Error {}

export class Store {
  users = new Map<number, User>();
  musics = new Map<number, Music>();
  playlists = new Map<number, Playlist>();
  private nextUser = 1;
  private nextMusic = 1;
  private nextPlaylist = 1;

  constructor() {
    [
      ["Ana Silva", "ana@example.com"],
      ["Bruno Costa", "bruno@example.com"],
      ["Carla Dias", "carla@example.com"],
    ].forEach(([name, email]) => this.createUser(name, email));

    [
      ["Song One", "Artist A", 210],
      ["Song Two", "Artist B", 185],
      ["Song Three", "Artist A", 240],
      ["Song Four", "Artist C", 199],
      ["Song Five", "Artist B", 300],
    ].forEach(([title, artist, duration]) =>
      this.createMusic(title as string, artist as string, duration as number),
    );

    this.createPlaylist("Favoritas da Ana", 1, [1, 2, 3]);
    this.createPlaylist("Treino do Bruno", 2, [2, 4]);
    this.createPlaylist("Chill da Carla", 3, [1, 5]);
    this.createPlaylist("Roadtrip da Ana", 1, [3, 5]);
  }

  // usuários
  listUsers(): User[] {
    return [...this.users.values()].sort((a, b) => a.id - b.id);
  }

  getUser(id: number): User {
    const user = this.users.get(id);
    if (!user) throw new NotFoundError(`usuário ${id} não encontrado`);
    return user;
  }

  createUser(name: string, email: string): User {
    const user = { id: this.nextUser++, name, email };
    this.users.set(user.id, user);
    return user;
  }

  updateUser(id: number, name?: string, email?: string): User {
    const user = this.getUser(id);
    if (name !== undefined) user.name = name;
    if (email !== undefined) user.email = email;
    return user;
  }

  deleteUser(id: number): boolean {
    if (!this.users.delete(id)) return false;
    for (const playlist of [...this.playlists.values()]) {
      if (playlist.ownerId === id) this.playlists.delete(playlist.id);
    }
    return true;
  }

  // músicas
  listMusics(): Music[] {
    return [...this.musics.values()].sort((a, b) => a.id - b.id);
  }

  getMusic(id: number): Music {
    const music = this.musics.get(id);
    if (!music) throw new NotFoundError(`música ${id} não encontrada`);
    return music;
  }

  createMusic(title: string, artist: string, durationSeconds: number): Music {
    const music = { id: this.nextMusic++, title, artist, durationSeconds };
    this.musics.set(music.id, music);
    return music;
  }

  updateMusic(id: number, title?: string, artist?: string, durationSeconds?: number): Music {
    const music = this.getMusic(id);
    if (title !== undefined) music.title = title;
    if (artist !== undefined) music.artist = artist;
    if (durationSeconds !== undefined) music.durationSeconds = durationSeconds;
    return music;
  }

  deleteMusic(id: number): boolean {
    if (!this.musics.delete(id)) return false;
    for (const playlist of this.playlists.values()) {
      playlist.musicIds = playlist.musicIds.filter((musicId) => musicId !== id);
    }
    return true;
  }

  // playlists
  listPlaylists(): Playlist[] {
    return [...this.playlists.values()].sort((a, b) => a.id - b.id);
  }

  getPlaylist(id: number): Playlist {
    const playlist = this.playlists.get(id);
    if (!playlist) throw new NotFoundError(`playlist ${id} não encontrada`);
    return playlist;
  }

  private validateRefs(ownerId: number, musicIds: number[]): void {
    if (!this.users.has(ownerId)) throw new ValidationError(`usuário ${ownerId} não existe`);
    for (const musicId of musicIds) {
      if (!this.musics.has(musicId)) throw new ValidationError(`música ${musicId} não existe`);
    }
  }

  createPlaylist(name: string, ownerId: number, musicIds: number[] = []): Playlist {
    this.validateRefs(ownerId, musicIds);
    const playlist = { id: this.nextPlaylist++, name, ownerId, musicIds: [...musicIds] };
    this.playlists.set(playlist.id, playlist);
    return playlist;
  }

  updatePlaylist(
    id: number,
    name?: string,
    ownerId?: number,
    musicIds?: number[],
  ): Playlist {
    const playlist = this.getPlaylist(id);
    const newOwner = ownerId ?? playlist.ownerId;
    const newMusics = musicIds ?? playlist.musicIds;
    this.validateRefs(newOwner, newMusics);
    if (name !== undefined) playlist.name = name;
    playlist.ownerId = newOwner;
    playlist.musicIds = [...newMusics];
    return playlist;
  }

  deletePlaylist(id: number): boolean {
    return this.playlists.delete(id);
  }

  // consultas relacionais
  playlistsByUser(userId: number): Playlist[] {
    return this.listPlaylists().filter((p) => p.ownerId === userId);
  }

  musicsByPlaylist(playlistId: number): Music[] {
    const playlist = this.getPlaylist(playlistId);
    return playlist.musicIds
      .map((id) => this.musics.get(id))
      .filter((m): m is Music => m !== undefined);
  }

  playlistsByMusic(musicId: number): Playlist[] {
    return this.listPlaylists().filter((p) => p.musicIds.includes(musicId));
  }
}

export const store = new Store();
