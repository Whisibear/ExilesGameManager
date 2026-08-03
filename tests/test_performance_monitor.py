from app.services import performance_monitor


def test_rates_returns_expected_keys():
    result = performance_monitor._rates()
    assert set(result) == {
        "networkUploadBytesPerSecond",
        "networkDownloadBytesPerSecond",
        "diskReadBytesPerSecond",
        "diskWriteBytesPerSecond",
    }
    assert all(value >= 0 for value in result.values())
