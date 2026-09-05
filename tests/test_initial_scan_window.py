from narra.scanner import initial_scan_bounds


def test_initial_scan_uses_latest_retained_window():
    low, high = initial_scan_bounds(server_first=10_000_000, server_last=12_000_000, limit=5000)
    assert (low, high) == (11_995_001, 12_000_000)


def test_initial_scan_never_starts_before_server_first():
    low, high = initial_scan_bounds(server_first=100, server_last=2500, limit=5000)
    assert (low, high) == (100, 2500)
