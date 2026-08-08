from __future__ import annotations

import socket
import struct
from dataclasses import dataclass

SERVERDATA_RESPONSE_VALUE = 0
SERVERDATA_EXECCOMMAND = 2
SERVERDATA_AUTH_RESPONSE = 2
SERVERDATA_AUTH = 3
MCRCON_REQUEST_ID = 0x0BADC0DE
MAX_PACKET_SIZE = 4 * 1024 * 1024
DEFAULT_TIMEOUT = 5.0
RESPONSE_IDLE_TIMEOUT = 0.45


class SourceRconError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SourceRconEndpoint:
    host: str
    port: int
    password: str


def encode_packet(request_id: int, packet_type: int, body: str) -> bytes:
    payload = struct.pack("<ii", request_id, packet_type) + body.encode("utf-8") + b"\x00\x00"
    return struct.pack("<i", len(payload)) + payload


def recv_exact(sock: socket.socket, length: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < length:
        chunk = sock.recv(length - len(chunks))
        if not chunk:
            raise SourceRconError("RCON connection closed unexpectedly.")
        chunks.extend(chunk)
    return bytes(chunks)


def read_packet(sock: socket.socket) -> tuple[int, int, str]:
    raw_size = recv_exact(sock, 4)
    (size,) = struct.unpack("<i", raw_size)
    if size < 10 or size > MAX_PACKET_SIZE:
        raise SourceRconError(f"Invalid RCON packet size: {size}.")
    payload = recv_exact(sock, size)
    request_id, packet_type = struct.unpack("<ii", payload[:8])
    body = payload[8:-2].decode("utf-8", errors="replace")
    return request_id, packet_type, body


def authenticate_mcrcon(sock: socket.socket, password: str, *, timeout: float = DEFAULT_TIMEOUT) -> int:
    request_id = MCRCON_REQUEST_ID
    sock.settimeout(timeout)
    sock.sendall(encode_packet(request_id, SERVERDATA_AUTH, password))
    try:
        response_id, _response_type, _body = read_packet(sock)
    except socket.timeout as exc:
        raise SourceRconError("RCON authentication response was not received.") from exc
    if response_id == -1:
        raise SourceRconError("RCON authentication failed.")
    return request_id


def collect_response(sock: socket.socket, request_id: int, *, timeout: float = DEFAULT_TIMEOUT) -> str:
    parts: list[str] = []
    received = False
    sock.settimeout(timeout)
    for _ in range(256):
        try:
            response_id, _response_type, body = read_packet(sock)
        except socket.timeout:
            break
        except SourceRconError as exc:
            if received and "closed unexpectedly" in str(exc).casefold():
                break
            raise
        if response_id != request_id:
            continue
        received = True
        if body:
            parts.append(body.rstrip("\x00"))
        sock.settimeout(RESPONSE_IDLE_TIMEOUT)
    return "".join(parts).rstrip("\x00")


def execute_mcrcon(
    endpoint: SourceRconEndpoint,
    command: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    cleaned = str(command).replace("\r", " ").replace("\n", " ").strip()
    if not cleaned:
        raise SourceRconError("RCON command must not be empty.")
    if len(cleaned.encode("utf-8")) >= 4096:
        raise SourceRconError("RCON command is too long.")
    try:
        with socket.create_connection((endpoint.host, endpoint.port), timeout=timeout) as sock:
            request_id = authenticate_mcrcon(sock, endpoint.password, timeout=timeout)
            sock.sendall(encode_packet(request_id, SERVERDATA_EXECCOMMAND, cleaned))
            return collect_response(sock, request_id, timeout=timeout)
    except SourceRconError:
        raise
    except (OSError, socket.timeout) as exc:
        raise SourceRconError(
            f"Could not communicate with RCON on {endpoint.host}:{endpoint.port}: {exc}"
        ) from exc
