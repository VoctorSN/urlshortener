import pytest

from app.services.shortcode import generate_short_code, is_valid_custom_alias
from app.services.qr_service import generate_qr_code
from app.services.analytics_service import parse_user_agent


class TestShortCodeGeneration:
    def test_generate_short_code_default_length(self):
        code = generate_short_code()
        assert len(code) == 7

    def test_generate_short_code_custom_length(self):
        code = generate_short_code(length=10)
        assert len(code) == 10

    def test_generate_short_code_uniqueness(self):
        codes = {generate_short_code() for _ in range(1000)}
        assert len(codes) == 1000

    def test_generate_short_code_url_safe(self):
        for _ in range(100):
            code = generate_short_code()
            assert all(c.isalnum() or c in "-_" for c in code)


class TestCustomAliasValidation:
    def test_valid_alias(self):
        assert is_valid_custom_alias("my-link") is True
        assert is_valid_custom_alias("test_123") is True
        assert is_valid_custom_alias("ABC") is True

    def test_too_short(self):
        assert is_valid_custom_alias("ab") is False

    def test_too_long(self):
        assert is_valid_custom_alias("a" * 31) is False

    def test_invalid_characters(self):
        assert is_valid_custom_alias("my link") is False
        assert is_valid_custom_alias("my@link") is False
        assert is_valid_custom_alias("my/link") is False

    def test_reserved_paths(self):
        assert is_valid_custom_alias("api") is False
        assert is_valid_custom_alias("health") is False
        assert is_valid_custom_alias("docs") is False
        assert is_valid_custom_alias("redoc") is False

    def test_reserved_case_insensitive(self):
        assert is_valid_custom_alias("API") is False
        assert is_valid_custom_alias("Health") is False


class TestQRCodeGeneration:
    def test_generates_bytes(self):
        data = generate_qr_code("https://example.com")
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_generates_valid_png(self):
        data = generate_qr_code("https://example.com")
        # PNG magic bytes
        assert data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_custom_size(self):
        small = generate_qr_code("https://example.com", size=5)
        large = generate_qr_code("https://example.com", size=20)
        assert len(large) > len(small)


class TestUserAgentParsing:
    def test_chrome_windows(self):
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        browser, os = parse_user_agent(ua)
        assert "Chrome" in browser
        assert "Windows" in os

    def test_firefox_linux(self):
        ua = "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
        browser, os = parse_user_agent(ua)
        assert "Firefox" in browser
        assert "Linux" in os

    def test_empty_string(self):
        browser, os = parse_user_agent("")
        assert isinstance(browser, str)
        assert isinstance(os, str)
