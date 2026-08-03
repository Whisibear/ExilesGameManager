from app.services import steamcmd


def test_redaction_hides_username_and_password_value():
    value = steamcmd._redact_text("password: secret SteamUser", "SteamUser")
    assert "secret" not in value
    assert "SteamUser" not in value


def test_auth_args_are_redacted():
    args = steamcmd._redact_args(["steamcmd.exe", "+login", "SteamUser", "secret", "+quit"])
    assert "SteamUser" not in args
    assert "secret" not in args
