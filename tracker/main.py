from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tracker.routes.tracker_routes import router as tracker_router

app = FastAPI(
    title="Mini P2P Tracker Server",
    description="Central coordination directory service for Peer-to-Peer file sharing.",
    version="1.0.0",
)

# Enable CORS for future frontend React dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(tracker_router)


@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "Welcome to Mini P2P Tracker Server",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("tracker.main:app", host="127.0.0.1", port=8000, reload=True)
