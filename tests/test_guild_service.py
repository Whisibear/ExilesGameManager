from app.services import guild_service


def test_decompress_level_save_uses_legacy_parser_for_plz(monkeypatch):
    expected = b"GVAS legacy"
    monkeypatch.setattr(
        guild_service,
        "decompress_sav_to_gvas",
        lambda raw: (expected, 0x31),
    )

    assert guild_service._decompress_level_save(b"\x00" * 8 + b"PlZ1payload") == expected


def test_decompress_level_save_supports_current_plm_format(monkeypatch):
    expected = b"GVAS current"
    compressed = b"oodle payload"
    raw = (
        len(expected).to_bytes(4, byteorder="little")
        + len(compressed).to_bytes(4, byteorder="little")
        + b"PlM1"
        + compressed
    )

    import ooz

    monkeypatch.setattr(
        ooz,
        "decompress",
        lambda payload, size: expected if (payload, size) == (compressed, len(expected)) else b"",
    )

    assert guild_service._decompress_level_save(raw) == expected


def test_decompress_level_save_rejects_truncated_plm():
    raw = (10).to_bytes(4, byteorder="little") + (20).to_bytes(4, byteorder="little") + b"PlM1short"

    try:
        guild_service._decompress_level_save(raw)
    except ValueError as exc:
        assert "incorrect PlM compressed length" in str(exc)
    else:
        raise AssertionError("truncated PlM save should have been rejected")
