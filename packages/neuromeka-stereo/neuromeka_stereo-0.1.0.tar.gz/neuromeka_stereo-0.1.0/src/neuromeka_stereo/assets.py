import hashlib
import os
import shutil
import tempfile
import urllib.request
from pathlib import Path
import importlib.resources as importlib_resources

DEFAULT_BASE_URL = "https://.../"
DEFAULT_ASSET_NAME = "foundation_stereo_RTX4060.plan"

ASSET_URLS = {
    "foundation_stereo_RTX4060.plan": "https://.../foundation_stereo_RTX4060.plan",
    "foundation_stereo_RTX5060.plan": "https://.../foundation_stereo_RTX5060.plan",
    "foundation_stereo_RTX5090.plan": "https://.../foundation_stereo_RTX5090.plan",
}

ASSET_SHA256 = {
    "foundation_stereo_RTX4060.plan": None,
    "foundation_stereo_RTX5060.plan": None,
    "foundation_stereo_RTX5090.plan": None,
}

GPU_ALIASES = {
    "RTX4060": "foundation_stereo_RTX4060.plan",
    "RTX5060": "foundation_stereo_RTX5060.plan",
    "RTX5090": "foundation_stereo_RTX5090.plan",
}


def resolve_asset_name(name):
    if not name:
        env_default = os.getenv("NEUROMEKA_STEREO_DEFAULT_PLAN")
        return env_default if env_default else DEFAULT_ASSET_NAME

    name = str(name).strip()
    if name in ASSET_URLS:
        return name

    normalized = name.replace(" ", "").upper()
    if normalized in GPU_ALIASES:
        return GPU_ALIASES[normalized]

    base = os.path.basename(name)
    if base in ASSET_URLS:
        return base

    return None


def _env_key_for_asset(name):
    key = name.replace(".", "_").replace("-", "_").upper()
    return f"NEUROMEKA_STEREO_ASSET_URL_{key}"


def get_asset_url(name):
    env_url = os.getenv(_env_key_for_asset(name))
    if env_url:
        return env_url

    base = os.getenv("NEUROMEKA_STEREO_ASSET_BASE_URL", "").strip()
    if base:
        if not base.endswith("/"):
            base = f"{base}/"
        return f"{base}{name}"

    return ASSET_URLS[name]


def get_cache_dir():
    env = os.getenv("NEUROMEKA_STEREO_CACHE_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".cache" / "neuromeka_stereo"


def _packaged_asset_path(name):
    try:
        path = importlib_resources.files("neuromeka_stereo").joinpath("assets", name)
        if path.is_file():
            return Path(path)
    except Exception:
        return None
    return None


def _local_asset_path(name):
    return Path(__file__).resolve().parent / "assets" / name


def _is_valid_asset(path):
    return path is not None and path.is_file() and path.stat().st_size > 0


def _auto_download_enabled(name):
    if os.getenv(_env_key_for_asset(name)):
        return True
    base = os.getenv("NEUROMEKA_STEREO_ASSET_BASE_URL", "").strip()
    return bool(base)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_asset(name):
    if name not in ASSET_URLS:
        raise ValueError(f"Unknown asset name: {name}")

    packaged = _packaged_asset_path(name)
    if _is_valid_asset(packaged):
        return str(packaged)

    local_path = _local_asset_path(name)
    if _is_valid_asset(local_path):
        return str(local_path)

    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / name
    if dest.exists() and dest.stat().st_size > 0:
        return str(dest)

    if not _auto_download_enabled(name):
        assets_dir = _local_asset_path(name).parent
        raise FileNotFoundError(
            f"Missing or empty asset '{name}'. Place it under '{assets_dir}' or '{cache_dir}' "
            "before running. Auto-download is disabled unless "
            "NEUROMEKA_STEREO_ASSET_BASE_URL or NEUROMEKA_STEREO_ASSET_URL_* is set."
        )

    url = get_asset_url(name)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=str(cache_dir), delete=False) as f:
            tmp = Path(f.name)
            with urllib.request.urlopen(url) as resp:
                shutil.copyfileobj(resp, f)
        expected = os.getenv(
            f"NEUROMEKA_STEREO_ASSET_SHA256_{name.replace('.', '_').upper()}",
            ASSET_SHA256.get(name) or "",
        ).strip()
        if expected:
            actual = _sha256(tmp)
            if actual.lower() != expected.lower():
                raise RuntimeError(
                    f"SHA256 mismatch for {name}: expected {expected}, got {actual}"
                )
        os.replace(tmp, dest)
    except Exception:
        if tmp and tmp.exists():
            tmp.unlink(missing_ok=True)
        raise

    return str(dest)
