from fastapi import FastAPI

app = FastAPI(
    title="ATLAS AI API",
    description="Cloud-first foundation API for a travel-agency multi-agent platform.",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app": "ATLAS AI",
        "mode": "foundation",
    }
