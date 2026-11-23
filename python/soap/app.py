"""Serviço de streaming de músicas - implementação SOAP 1.1 (document/literal).

Contrato: specs/music-service.wsdl (servido em GET /?wsdl)
Execução (a partir de python/):
    uvicorn soap.app:app --host 0.0.0.0 --port 8001

Observação: o Spyne 2.14 não funciona no Python 3.12 (usa APIs de import removidas),
então o envelope SOAP é montado/parseado diretamente com xml.etree. Isso também deixa
explícita a verbosidade do protocolo, útil na análise comparativa do trabalho.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET

from fastapi import FastAPI, Request, Response

from common.store import NotFoundError, ValidationError, store

SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
TNS = "http://music.example.com/wsdl"
WSDL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "specs",
    "music-service.wsdl",
)

ET.register_namespace("soap", SOAP_NS)
ET.register_namespace("tns", TNS)

app = FastAPI(title="Music Streaming Service (SOAP)", version="1.0.0")


class SoapFault(Exception):
    def __init__(self, message: str, code: str = "soap:Server"):
        super().__init__(message)
        self.message = message
        self.code = code


# ------------------------------------------------------------- serialização
def tag(name: str) -> str:
    return f"{{{TNS}}}{name}"


def text_elem(parent: ET.Element, name: str, value) -> ET.Element:
    elem = ET.SubElement(parent, tag(name))
    elem.text = str(value)
    return elem


def user_elem(parent: ET.Element, name: str, u) -> ET.Element:
    elem = ET.SubElement(parent, tag(name))
    text_elem(elem, "id", u.id)
    text_elem(elem, "name", u.name)
    text_elem(elem, "email", u.email)
    return elem


def music_elem(parent: ET.Element, name: str, m) -> ET.Element:
    elem = ET.SubElement(parent, tag(name))
    text_elem(elem, "id", m.id)
    text_elem(elem, "title", m.title)
    text_elem(elem, "artist", m.artist)
    text_elem(elem, "durationSeconds", m.duration_seconds)
    return elem


def playlist_elem(parent: ET.Element, name: str, p) -> ET.Element:
    elem = ET.SubElement(parent, tag(name))
    text_elem(elem, "id", p.id)
    text_elem(elem, "name", p.name)
    text_elem(elem, "ownerId", p.owner_id)
    for music_id in p.music_ids:
        text_elem(elem, "musicIds", music_id)
    return elem


def new_response(op: str) -> ET.Element:
    return ET.Element(tag(f"{op}Response"))


def serialize(response: ET.Element) -> bytes:
    envelope = ET.Element(f"{{{SOAP_NS}}}Envelope")
    body = ET.SubElement(envelope, f"{{{SOAP_NS}}}Body")
    body.append(response)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def fault(message: str, code: str = "soap:Server") -> bytes:
    fault_el = ET.Element(f"{{{SOAP_NS}}}Fault")
    ET.SubElement(fault_el, "faultcode").text = code
    ET.SubElement(fault_el, "faultstring").text = message
    return serialize(fault_el)


# --------------------------------------------------------------- operações
def op_list_users(_: dict) -> ET.Element:
    resp = new_response("ListUsers")
    for u in store.list_users():
        user_elem(resp, "users", u)
    return resp


def op_get_user(args: dict) -> ET.Element:
    try:
        user = store.get_user(args["id"])
    except NotFoundError as exc:
        raise SoapFault(str(exc), "soap:Client")
    resp = new_response("GetUser")
    user_elem(resp, "user", user)
    return resp


def op_create_user(args: dict) -> ET.Element:
    resp = new_response("CreateUser")
    user_elem(resp, "user", store.create_user(args["name"], args["email"]))
    return resp


def op_update_user(args: dict) -> ET.Element:
    try:
        user = store.update_user(args["id"], args.get("name"), args.get("email"))
    except NotFoundError as exc:
        raise SoapFault(str(exc), "soap:Client")
    resp = new_response("UpdateUser")
    user_elem(resp, "user", user)
    return resp


def op_delete_user(args: dict) -> ET.Element:
    resp = new_response("DeleteUser")
    text_elem(resp, "deleted", "true" if store.delete_user(args["id"]) else "false")
    return resp


def op_list_musics(_: dict) -> ET.Element:
    resp = new_response("ListMusics")
    for m in store.list_musics():
        music_elem(resp, "musics", m)
    return resp


def op_get_music(args: dict) -> ET.Element:
    try:
        music = store.get_music(args["id"])
    except NotFoundError as exc:
        raise SoapFault(str(exc), "soap:Client")
    resp = new_response("GetMusic")
    music_elem(resp, "music", music)
    return resp


def op_create_music(args: dict) -> ET.Element:
    resp = new_response("CreateMusic")
    music_elem(
        resp,
        "music",
        store.create_music(args["title"], args["artist"], args["durationSeconds"]),
    )
    return resp


def op_update_music(args: dict) -> ET.Element:
    try:
        music = store.update_music(
            args["id"], args.get("title"), args.get("artist"), args.get("durationSeconds")
        )
    except NotFoundError as exc:
        raise SoapFault(str(exc), "soap:Client")
    resp = new_response("UpdateMusic")
    music_elem(resp, "music", music)
    return resp


def op_delete_music(args: dict) -> ET.Element:
    resp = new_response("DeleteMusic")
    text_elem(resp, "deleted", "true" if store.delete_music(args["id"]) else "false")
    return resp


def op_list_playlists(_: dict) -> ET.Element:
    resp = new_response("ListPlaylists")
    for p in store.list_playlists():
        playlist_elem(resp, "playlists", p)
    return resp


def op_get_playlist(args: dict) -> ET.Element:
    try:
        playlist = store.get_playlist(args["id"])
    except NotFoundError as exc:
        raise SoapFault(str(exc), "soap:Client")
    resp = new_response("GetPlaylist")
    playlist_elem(resp, "playlist", playlist)
    return resp


def op_create_playlist(args: dict) -> ET.Element:
    try:
        playlist = store.create_playlist(
            args["name"], args["ownerId"], args.get("musicIds", [])
        )
    except ValidationError as exc:
        raise SoapFault(str(exc), "soap:Client")
    resp = new_response("CreatePlaylist")
    playlist_elem(resp, "playlist", playlist)
    return resp


def op_update_playlist(args: dict) -> ET.Element:
    try:
        playlist = store.update_playlist(
            args["id"], args.get("name"), args.get("ownerId"), args.get("musicIds")
        )
    except NotFoundError as exc:
        raise SoapFault(str(exc), "soap:Client")
    except ValidationError as exc:
        raise SoapFault(str(exc), "soap:Client")
    resp = new_response("UpdatePlaylist")
    playlist_elem(resp, "playlist", playlist)
    return resp


def op_delete_playlist(args: dict) -> ET.Element:
    resp = new_response("DeletePlaylist")
    text_elem(resp, "deleted", "true" if store.delete_playlist(args["id"]) else "false")
    return resp


def op_playlists_by_user(args: dict) -> ET.Element:
    resp = new_response("ListPlaylistsByUser")
    for p in store.playlists_by_user(args["userId"]):
        playlist_elem(resp, "playlists", p)
    return resp


def op_musics_by_playlist(args: dict) -> ET.Element:
    try:
        musics = store.musics_by_playlist(args["playlistId"])
    except NotFoundError as exc:
        raise SoapFault(str(exc), "soap:Client")
    resp = new_response("ListMusicsByPlaylist")
    for m in musics:
        music_elem(resp, "musics", m)
    return resp


def op_playlists_by_music(args: dict) -> ET.Element:
    resp = new_response("ListPlaylistsByMusic")
    for p in store.playlists_by_music(args["musicId"]):
        playlist_elem(resp, "playlists", p)
    return resp


OPERATIONS = {
    "ListUsers": op_list_users,
    "GetUser": op_get_user,
    "CreateUser": op_create_user,
    "UpdateUser": op_update_user,
    "DeleteUser": op_delete_user,
    "ListMusics": op_list_musics,
    "GetMusic": op_get_music,
    "CreateMusic": op_create_music,
    "UpdateMusic": op_update_music,
    "DeleteMusic": op_delete_music,
    "ListPlaylists": op_list_playlists,
    "GetPlaylist": op_get_playlist,
    "CreatePlaylist": op_create_playlist,
    "UpdatePlaylist": op_update_playlist,
    "DeletePlaylist": op_delete_playlist,
    "ListPlaylistsByUser": op_playlists_by_user,
    "ListMusicsByPlaylist": op_musics_by_playlist,
    "ListPlaylistsByMusic": op_playlists_by_music,
}

INT_FIELDS = {"id", "durationSeconds", "ownerId", "userId", "playlistId", "musicId"}
LIST_FIELDS = {"musicIds"}


# ---------------------------------------------------------------- parsing
def parse_body(xml_bytes: bytes) -> tuple[str, dict]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise SoapFault(f"XML inválido: {exc}", "soap:Client")

    body = root.find(f"{{{SOAP_NS}}}Body")
    if body is None or len(body) == 0:
        raise SoapFault("Envelope SOAP sem Body/operação", "soap:Client")

    operation = list(body)[0]
    op_name = operation.tag.split("}")[-1]
    args: dict = {}
    for child in operation:
        name = child.tag.split("}")[-1]
        value = (child.text or "").strip()
        if name in LIST_FIELDS:
            args.setdefault(name, []).append(int(value))
        elif name in INT_FIELDS:
            args[name] = int(value)
        else:
            args[name] = value
    return op_name, args


# ------------------------------------------------------------------- rotas
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def wsdl(request: Request):
    if "wsdl" in request.query_params or request.url.path.endswith(".wsdl"):
        with open(WSDL_PATH, "rb") as fh:
            return Response(content=fh.read(), media_type="text/xml")
    return Response(
        content="MusicService SOAP: envie POST com um envelope SOAP ou GET /?wsdl",
        media_type="text/plain",
    )


@app.post("/")
async def soap_endpoint(request: Request):
    raw = await request.body()
    try:
        op_name, args = parse_body(raw)
        handler = OPERATIONS.get(op_name)
        if handler is None:
            raise SoapFault(f"Operação desconhecida: {op_name}", "soap:Client")
        response = handler(args)
        return Response(content=serialize(response), media_type="text/xml; charset=utf-8")
    except SoapFault as exc:
        return Response(
            content=fault(exc.message, exc.code),
            status_code=500,
            media_type="text/xml; charset=utf-8",
        )
