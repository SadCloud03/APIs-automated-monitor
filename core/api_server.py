from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from urllib.parse import urlparse

from core.logic import (
    add_API_database,
    delete_api,
    get_api,
    get_apis_with_state,
    get_logs,
    get_overview_stats,
)

app = FastAPI(title="API Monitor Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ApiCreate(BaseModel):
    name: str
    url: str


def _valid_url(u: str) -> bool:
    try:
        p = urlparse(u.strip())
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/stats/overview")
def overview():
    return get_overview_stats()


@app.get("/apis")
def list_apis():
    return get_apis_with_state()


@app.get("/apis/{api_id}")
def api_detail(api_id: int):
    a = get_api(api_id)
    if not a:
        raise HTTPException(status_code=404, detail="API not found")
    return a


@app.get("/apis/{api_id}/logs")
def api_logs(
    api_id: int,
    limit: int = Query(200, ge=1, le=2000),
    since: str | None = None,
    until: str | None = None,
):
    a = get_api(api_id)
    if not a:
        raise HTTPException(status_code=404, detail="API not found")
    return get_logs(api_id, limit=limit, since=since, until=until)


@app.post("/apis")
def create_api(payload: ApiCreate):
    try:
        add_API_database(payload.name.strip(), payload.url.strip())
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/apis/{api_id}")
def remove_api(api_id: int):
    a = get_api(api_id)
    if not a:
        raise HTTPException(status_code=404, detail="API not found")
    delete_api(api_id)
    return {"ok": True}


@app.post("/apis/upload")
async def upload_apis(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Subí un archivo .txt")

    raw = (await file.read()).decode("utf-8", errors="ignore")

    added = 0
    skipped = 0
    errors = []

    for lineno, line in enumerate(raw.splitlines(), start=1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue

        name = None
        url = s

        if "|" in s:
            name, url = [x.strip() for x in s.split("|", 1)]
            if not name:
                name = None

        url = url.strip()
        if not _valid_url(url):
            skipped += 1
            errors.append({"line": lineno, "value": s, "error": "URL inválida"})
            continue

        final_name = (name or url).strip()

        try:
            add_API_database(final_name, url)
            added += 1
        except ValueError as e:
            skipped += 1
            errors.append({"line": lineno, "value": s, "error": str(e)})
        except Exception as e:
            skipped += 1
            errors.append({"line": lineno, "value": s, "error": f"Unexpected: {e}"})

    if added == 0:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "No se pudo cargar ninguna API válida",
                "errors": errors[:50],
            },
        )

    return {"ok": True, "added": added, "skipped": skipped, "errors": errors[:50]}
