from __future__ import annotations

from typing import Any

from app.games import get_game_or_default
from app.games.providers.base import GameProvider
from app.games.providers.conan import ConanProvider
from app.games.providers.palworld import PalworldProvider


class ProviderUnavailableError(RuntimeError):
    def __init__(self, game_id: str, game_label: str):
        super().__init__(
            f"{game_label} is registered but its runtime provider "
            "is not available in this build."
        )
        self.game_id = game_id
        self.game_label = game_label


_PROVIDERS: dict[str, GameProvider] = {
    "palworld": PalworldProvider(),
    "conan_exiles_enhanced": ConanProvider(
        "conan_exiles_enhanced",
        "enhanced",
    ),
    "conan_exiles_legacy": ConanProvider(
        "conan_exiles_legacy",
        "legacy",
    ),
}

_RUNTIME_READY = frozenset({"palworld", "conan_exiles_enhanced", "conan_exiles_legacy"})


def get_provider_for_game(game_id: str) -> GameProvider:
    game = get_game_or_default(game_id)
    provider = _PROVIDERS.get(game.id)
    if provider is None:
        raise ProviderUnavailableError(game.id, game.label)
    return provider


def get_provider_for_instance(
    instance: dict[str, Any],
) -> GameProvider:
    game = get_game_or_default(instance.get("gameId"))
    if game.id not in _RUNTIME_READY:
        raise ProviderUnavailableError(game.id, game.label)
    return get_provider_for_game(game.id)
