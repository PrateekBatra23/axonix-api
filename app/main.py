from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import digests

app = FastAPI(title="Frontier")

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(digests.router)

@app.get("/health")
def health():
    return {"status": "ok"}