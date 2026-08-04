from __future__ import annotations

import ast
from pathlib import Path

KERNEL_ROOT = (
    Path(__file__).resolve().parents[2] / "src" / "stock_market_analyzer" / "shared" / "kernel"
)
PACKAGE_ROOT = KERNEL_ROOT.parent.parent
INSTRUMENTS_ROOT = PACKAGE_ROOT / "modules" / "instruments"
MARKET_DATA_ROOT = PACKAGE_ROOT / "modules" / "market_data"

FORBIDDEN_KERNEL_IMPORT_ROOTS = {
    "fastapi",
    "sqlalchemy",
    "redis",
    "uvicorn",
    "pydantic_settings",
}


def _collect_import_roots(file_path: Path) -> set[str]:
    module = ast.parse(file_path.read_text(encoding="utf-8"))
    import_roots: set[str] = set()

    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            import_roots.add(node.module.split(".")[0])

    return import_roots


def test_shared_kernel_does_not_import_framework_or_infrastructure_packages() -> None:
    python_files = list(KERNEL_ROOT.rglob("*.py"))
    assert python_files, "Expected shared kernel Python modules to exist."

    violations: list[str] = []

    for file_path in python_files:
        forbidden = _collect_import_roots(file_path) & FORBIDDEN_KERNEL_IMPORT_ROOTS
        if forbidden:
            relative_path = file_path.relative_to(PACKAGE_ROOT)
            violations.append(f"{relative_path}: {sorted(forbidden)}")

    assert violations == []


def test_instrument_core_does_not_import_frameworks_or_infrastructure() -> None:
    protected_roots = (
        INSTRUMENTS_ROOT / "application",
        INSTRUMENTS_ROOT / "domain",
        INSTRUMENTS_ROOT / "ports",
    )
    python_files = [
        file_path
        for protected_root in protected_roots
        for file_path in protected_root.rglob("*.py")
    ]
    assert python_files, "Expected instrument domain and port modules to exist."

    violations: list[str] = []
    for file_path in python_files:
        import_roots = _collect_import_roots(file_path)
        forbidden = import_roots & FORBIDDEN_KERNEL_IMPORT_ROOTS
        source = file_path.read_text(encoding="utf-8")
        if forbidden or ".infrastructure" in source:
            relative_path = file_path.relative_to(PACKAGE_ROOT)
            violations.append(f"{relative_path}: {sorted(forbidden)}")

    assert violations == []


def test_market_data_core_does_not_import_frameworks_or_other_modules() -> None:
    protected_roots = (
        MARKET_DATA_ROOT / "application",
        MARKET_DATA_ROOT / "domain",
        MARKET_DATA_ROOT / "ports",
    )
    python_files = [
        file_path
        for protected_root in protected_roots
        for file_path in protected_root.rglob("*.py")
    ]
    assert python_files, "Expected market-data domain, application, and port modules to exist."

    violations: list[str] = []
    for file_path in python_files:
        import_roots = _collect_import_roots(file_path)
        forbidden = import_roots & FORBIDDEN_KERNEL_IMPORT_ROOTS
        source = file_path.read_text(encoding="utf-8")
        if forbidden or ".infrastructure" in source or ".modules.instruments" in source:
            relative_path = file_path.relative_to(PACKAGE_ROOT)
            violations.append(f"{relative_path}: {sorted(forbidden)}")

    assert violations == []
