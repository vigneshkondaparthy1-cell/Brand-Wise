import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("================================================================")
    print(f"  Starting {settings.APP_TITLE} (FastAPI + Uvicorn)")
    print(f"  API Docs: http://{settings.HOST}:{settings.PORT}/api/docs")
    print(f"  Web App:  http://{settings.HOST}:{settings.PORT}/")
    print("================================================================")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
