"""The repository has one version: VERSION at its root, shared by the Python and C++ clients."""
import re
from pathlib import Path

import libfinance

ROOT = Path(__file__).resolve().parents[2]


def test_python_reports_the_repository_version():
    assert libfinance.__version__ == (ROOT / "VERSION").read_text().strip()


def test_python_and_cpp_read_the_same_file():
    assert (ROOT / "python" / "VERSION").resolve() == (ROOT / "VERSION").resolve()
    assert 'version = {file = "VERSION"}' in (ROOT / "python" / "pyproject.toml").read_text()
    cmake = (ROOT / "cpp" / "CMakeLists.txt").read_text()
    assert re.search(r'file\(STRINGS "\$\{CMAKE_CURRENT_SOURCE_DIR\}/\.\./VERSION"', cmake)
    assert re.search(r"project\(libfinance VERSION \$\{LIBFINANCE_VERSION_FROM_FILE\}", cmake)


def test_the_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", (ROOT / "VERSION").read_text().strip())
