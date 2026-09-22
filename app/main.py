import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


def database_url() -> str:
    if value := os.getenv("DATABASE_URL"):
        return value
    return (
        f"postgresql+psycopg://{os.getenv('DB_USER', 'appuser')}:"
        f"{os.getenv('DB_PASSWORD', 'appsecret')}@{os.getenv('DB_HOST', 'db')}:"
        f"{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'app')}"
    )


url = database_url()
engine_options = {"pool_pre_ping": True}
if url.startswith("sqlite"):
    engine_options.update(connect_args={"check_same_thread": False}, poolclass=StaticPool)
engine = create_engine(url, **engine_options)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(500), default="")


class ItemInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class ItemView(ItemInput):
    id: int
    model_config = ConfigDict(from_attributes=True)


def get_session():
    with SessionLocal() as session:
        yield session


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        if not session.scalar(select(Item).limit(1)):
            session.add(Item(name="seed-item", description="Created for this preview database"))
            session.commit()
    yield


app = FastAPI(title=os.getenv("SERVICE_NAME", "orders-service"), lifespan=lifespan)


@app.middleware("http")
async def strip_alb_prefix(request, call_next):
    """The shared ALB exposes this service below /a or /b without app-specific routes."""
    prefix = os.getenv("PATH_PREFIX", "")
    if prefix and request.scope["path"].startswith(prefix):
        request.scope["path"] = request.scope["path"][len(prefix) :] or "/"
    return await call_next(request)


@app.get("/health")
def health(session: Session = Depends(get_session)):
    session.execute(select(1))
    return {"status": "ok", "service": app.title}


@app.get("/items", response_model=list[ItemView])
def list_items(session: Session = Depends(get_session)):
    return list(session.scalars(select(Item).order_by(Item.id)))


@app.post("/items", response_model=ItemView, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemInput, session: Session = Depends(get_session)):
    if session.scalar(select(Item).where(Item.name == payload.name)):
        raise HTTPException(status_code=409, detail="Item name already exists")
    item = Item(**payload.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@app.get("/items/{item_id}", response_model=ItemView)
def get_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.put("/items/{item_id}", response_model=ItemView)
def update_item(item_id: int, payload: ItemInput, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.name, item.description = payload.name, payload.description
    session.commit()
    session.refresh(item)
    return item


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(item)
    session.commit()
