from narra.nntp import overview_bounds


def test_initial_scan_uses_latest_retained_window():
    low, high = overview_bounds(server_first=10_000_000, server_last=12_000_000, start=None, limit=5000)
    assert (low, high) == (11_995_001, 12_000_000)


def test_initial_scan_never_starts_before_server_first():
    low, high = overview_bounds(server_first=100, server_last=2500, start=None, limit=5000)
    assert (low, high) == (100, 2500)


def test_incremental_scan_starts_after_saved_high_water():
    low, high = overview_bounds(server_first=100, server_last=20_000, start=12_346, limit=5000)
    assert (low, high) == (12_346, 17_345)
