from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.logic import (
    add_API_database,
    delete_api,
    get_api,
    get_apis_with_state,
    get_logs,
    get_overview_stats,
)

app = FastAPI(title="API Monitor Dashboard", version="1.0.0")

# En producción: restringí allow_origins a tu dominio real
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
        add_API_database(payload.name, payload.url)
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
