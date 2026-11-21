from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from .config import settings
from .store import store
from .routers import audits, claims, guidelines, visual, insights, integrations, auth, keys

app = FastAPI(
    title=settings.APP_TITLE,
    description="A pre-publication review platform that checks content against approved brand guidelines, facts and assets: grounded, explainable and human-controlled.",
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)
app.mount('/static', StaticFiles(directory=settings.FRONTEND_FILE.parent / 'static'), name='static')

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(audits.router)
app.include_router(claims.router)
app.include_router(guidelines.router)
app.include_router(visual.router)
app.include_router(insights.router)
app.include_router(integrations.router)
app.include_router(auth.router)
app.include_router(keys.router)

@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "ok": True,
        "service": settings.APP_TITLE,
        "version": settings.VERSION,
        "workingTitle": settings.APP_NAME,
        "preparedBy": settings.PREPARED_BY,
        "disclosedAI": settings.DISCLOSED_MODELS,
        "zeroRetention": settings.ZERO_DATA_RETENTION_TRAINING,
        "tenantIsolation": settings.TENANT_ISOLATION_ENABLED
    }

@app.post("/api/reset", tags=["System"])
def reset_database():
    store.reset_all()
    return {"ok": True, "message": "Demo data reset to official BrandWise proposal seed"}

# Root Endpoint: Serves the Web App Frontend
@app.get("/", response_class=HTMLResponse, tags=["Web Application"])
def serve_web_app():
    if settings.FRONTEND_FILE.exists():
        return HTMLResponse(content=settings.FRONTEND_FILE.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>BrandWise Backend API is running. Open /api/docs for OpenAPI documentation.</h1>")

@app.get("/index.html", response_class=HTMLResponse, tags=["Web Application"])
def serve_index():
    return serve_web_app()
