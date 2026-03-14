from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import connect_to_db, close_db_connection
from app.api.routes import champions
from app.api.routes import jaw
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import certification
from app.api.routes import feedback

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_db()  # Startup logic
    yield  # Waits until the app shuts down
    await close_db_connection()  # Cleanup logic

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from localhost:3000
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(champions.router, prefix="/api")
app.include_router(jaw.router, prefix="/api")
app.include_router(certification.router, prefix="/api")
app.include_router(certification.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
