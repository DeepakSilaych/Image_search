from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine, Base
from app.api.routes import images, search, faces, events, stats


def _run_migrations():
    from sqlalchemy import text, inspect
    with engine.connect() as conn:
        inspector = inspect(engine)
        if "persons" in inspector.get_table_names():
            cols = {c["name"] for c in inspector.get_columns("persons")}
            if "is_auto" not in cols:
                conn.execute(text("ALTER TABLE persons ADD COLUMN is_auto BOOLEAN DEFAULT FALSE"))
                conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _run_migrations()
    yield


app = FastAPI(title="Image Search Engine", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(images.router, prefix="/api/images", tags=["images"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(faces.router, prefix="/api/faces", tags=["faces"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
