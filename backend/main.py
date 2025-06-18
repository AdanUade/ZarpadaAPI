from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.sample import router as sample_router
import uvicorn, os                       # ← 1

app = FastAPI(title="Zarpado API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sample_router)

@app.get("/")                            # health-check
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),  # ← 2
        reload=True                              # reload sólo en local
    )
