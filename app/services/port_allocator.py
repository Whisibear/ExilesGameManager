from __future__ import annotations
import socket
from dataclasses import dataclass
from typing import Iterable
from app.games import require_game
from app.games.providers import get_provider_for_game
from app.games.models import GameDefinition, PortDefinition

class PortAllocationError(ValueError): pass

@dataclass(frozen=True, slots=True)
class PortReservation:
    key: str; label: str; port: int; protocol: str; configurable: bool; firewall: bool
    def to_dict(self):
        return {"key":self.key,"label":self.label,"port":self.port,"protocol":self.protocol,
                "configurable":self.configurable,"firewall":self.firewall}

def _port(value):
    try: value=int(value)
    except (TypeError,ValueError): return None
    return value if 1 <= value <= 65535 else None

def _available(port:int, protocol:str)->bool:
    kind=socket.SOCK_STREAM if protocol=="TCP" else socket.SOCK_DGRAM
    sock=socket.socket(socket.AF_INET,kind)
    try:
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,0)
        sock.bind(("0.0.0.0",port))
        if protocol=="TCP": sock.listen(1)
        return True
    except OSError: return False
    finally: sock.close()

def instance_ports(instance):
    game_id = str(instance.get("gameId") or "palworld")
    return get_provider_for_game(game_id).network.resolve_ports(instance)

def reserved_ports(instances:Iterable[dict],exclude_id=None):
    result=set()
    for instance in instances:
        if exclude_id and instance.get("id")==exclude_id: continue
        result.update(instance_ports(instance).values())
    return result

def validate_port_map(game:GameDefinition, ports:dict[str,int], *, reserved=None, check_host=False):
    reserved=reserved or set(); selected={}; rows=[]
    for definition in get_provider_for_game(game.id).network.port_definitions:
        if definition.relative_to:
            expected=selected[definition.relative_to]+definition.offset
            value=int(ports.get(definition.key,expected))
            if value != expected:
                raise PortAllocationError(f"{definition.label} must be {definition.relative_to} + {definition.offset}.")
        else:
            value=int(ports.get(definition.key,definition.default))
        if not 1 <= value <= 65535: raise PortAllocationError(f"{definition.label} must be between 1 and 65535.")
        if value in selected.values(): raise PortAllocationError(f"{definition.label} conflicts with another selected port.")
        if value in reserved: raise PortAllocationError(f"{definition.label} {value} is already reserved by another server.")
        if check_host and not _available(value,definition.protocol):
            raise PortAllocationError(f"{definition.label} {value}/{definition.protocol} is already in use on this machine.")
        selected[definition.key]=value
        rows.append(PortReservation(definition.key,definition.label,value,definition.protocol,definition.configurable,definition.firewall))
    return rows

def suggest_ports(game_id:str, instances:Iterable[dict]):
    game=require_game(game_id); provider=get_provider_for_game(game_id); definitions=provider.network.port_definitions; reserved=reserved_ports(instances); selected={}; rows=[]
    for definition in definitions:
        if definition.relative_to:
            value=selected[definition.relative_to]+definition.offset
            if value in reserved or not _available(value,definition.protocol):
                parent=next(p for p in definitions if p.key==definition.relative_to)
                candidate=selected[parent.key]
                while True:
                    candidate += 1
                    related=candidate+definition.offset
                    if candidate not in reserved and related not in reserved and _available(candidate,parent.protocol) and _available(related,definition.protocol):
                        selected[parent.key]=candidate
                        rows=[PortReservation(x.key,x.label,candidate if x.key==parent.key else x.port,x.protocol,x.configurable,x.firewall) for x in rows]
                        value=related; break
        else:
            value=definition.default
            while value in reserved or value in selected.values() or not _available(value,definition.protocol):
                value += 1
                if value>65535: raise PortAllocationError(f"No free port found for {definition.label}.")
        selected[definition.key]=value
        rows.append(PortReservation(definition.key,definition.label,value,definition.protocol,definition.configurable,definition.firewall))
    validate_port_map(game,selected,reserved=reserved,check_host=True)
    return rows
