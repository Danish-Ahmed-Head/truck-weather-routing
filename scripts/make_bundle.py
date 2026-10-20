"""Zip backend/ (with the built frontend) for hosts that take an upload instead of a git clone.

Run `npm run build` in frontend/ first. Output: deploy/truck-routing-bundle.zip, unpacking to truck-routing/backend/.
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
SKIP_DIRS = {".venv", "__pycache__", "staticfiles", ".ruff_cache"}
OUT = ROOT / "deploy" / "truck-routing-bundle.zip"

if not (BACKEND / "frontend_dist" / "index.html").exists():
    raise SystemExit("backend/frontend_dist is missing: run `npm run build` in frontend/ first.")

OUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
    for path in sorted(BACKEND.rglob("*")):
        rel = path.relative_to(BACKEND)
        if path.is_file() and not SKIP_DIRS.intersection(rel.parts) and path.suffix != ".pyc":
            zf.write(path, Path("truck-routing") / "backend" / rel)
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
