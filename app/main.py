from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import digests
from app.routers import stories
from app.routers import jobs
from app.routers import (
    digests, stories, jobs,
    auth, users, settings, dashboard, scrape_runs, companies,
)


app = FastAPI(title="Frontier")

origins = []

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(settings.router)
app.include_router(dashboard.router)
app.include_router(scrape_runs.router)
app.include_router(companies.router)
app.include_router(companies.public_router)
app.include_router(digests.router)
app.include_router(stories.router)
app.include_router(jobs.router)

@app.get("/health")
def health():
    return {"status": "ok"}