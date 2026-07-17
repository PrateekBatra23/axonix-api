from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import digests
from app.routers import stories
from app.routers import jobs

app = FastAPI(title="Frontier")

origins = [
    "http://localhost:3000",
    "https://axonix-web.vercel.app"
    "https://avonzi.prateekbatra.dev",
    "https://avonzi.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(digests.router)
app.include_router(stories.router)
app.include_router(jobs.router)

@app.get("/health")
def health():
    return {"status": "ok"}