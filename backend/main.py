from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.sample import router as sample_router

app = FastAPI(title="Zarpado API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sample_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
