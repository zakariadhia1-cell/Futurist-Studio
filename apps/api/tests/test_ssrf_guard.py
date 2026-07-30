from app.orchestrator.tools.ssrf_guard import is_safe_url


def test_rejects_loopback():
    assert is_safe_url("http://localhost:8000/") is False
    assert is_safe_url("http://127.0.0.1/") is False


def test_rejects_private_ranges():
    assert is_safe_url("http://10.0.0.5/") is False
    assert is_safe_url("http://192.168.1.1/") is False


def test_rejects_link_local_metadata_endpoint():
    # 169.254.169.254 is the AWS/GCP/Azure cloud metadata endpoint - a classic SSRF target.
    assert is_safe_url("http://169.254.169.254/latest/meta-data/") is False


def test_rejects_non_http_schemes():
    assert is_safe_url("file:///etc/passwd") is False
    assert is_safe_url("ftp://8.8.8.8/") is False


def test_accepts_public_ip_literal():
    assert is_safe_url("http://8.8.8.8/") is True
