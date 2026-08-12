
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import Base, engine
from routers.transactions import router as transaction_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables when application starts.
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(
    title="Transaction API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(transaction_router)


@app.get("/health")
async def health():
    return {"status": "ok"}