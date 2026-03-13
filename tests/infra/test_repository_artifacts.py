from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_security_audit_prompt_exists_with_core_sections() -> None:
    prompt_path = REPO_ROOT / ".github" / "prompts" / "security-audit.prompt.md"
    assert prompt_path.is_file()

    content = _read_text(".github/prompts/security-audit.prompt.md")
    normalized = content.lower()

    assert "description:" in normalized
    assert "name:" in normalized
    assert "agent:" in normalized

    assert "secretos" in normalized
    assert "autenticacion" in normalized or "autorizacion" in normalized
    assert "controles de acceso" in normalized
    assert "sanitizadas" in normalized or "validadas" in normalized
    assert "ssrf" in normalized


def test_security_audit_prompt_requires_security_report_output() -> None:
    content = _read_text(".github/prompts/security-audit.prompt.md")
    normalized = content.lower()

    assert "requisitos de salida" in normalized
    assert "security.md" in content
    assert "severidad" in normalized
    assert "evidencia" in normalized
    assert "remediacion" in normalized
    assert "positive security notes" in normalized


def test_gitignore_does_not_ignore_security_report_artifact() -> None:
    content = _read_text(".gitignore")
    entries = {
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert "security.md" not in entries


def test_license_file_has_mit_header() -> None:
    license_path = REPO_ROOT / "LICENSE"
    assert license_path.is_file()

    content = _read_text("LICENSE")
    assert content.startswith("MIT License")
    assert "Permission is hereby granted, free of charge" in content
