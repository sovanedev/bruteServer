import uvicorn
from routers import app

if __name__ == "__main__":
    uvicorn.run(
        "routers:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
