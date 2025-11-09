"""
Main FastAPI application for GC Video Scope Analyzer
Multi-tenant SaaS version
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config.settings import settings
from config.supabase import get_supabase, get_supabase_admin
from models.schemas import SuccessResponse, ErrorResponse
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-tenant scope analysis SaaS for general contractors"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# HEALTH CHECK & STATUS
# =====================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Supabase connection
        supabase = get_supabase()
        # Simple query to verify connection
        supabase.table('clients').select('id').limit(1).execute()

        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# =====================================================
# IMPORT ROUTES
# =====================================================

# Import route modules (will be created next)
# from routes import auth, projects, files, analyses, documents, clients

# Include routers
# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
# app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
# app.include_router(files.router, prefix="/api/files", tags=["Files"])
# app.include_router(analyses.router, prefix="/api/analyses", tags=["Analyses"])
# app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])


# =====================================================
# ERROR HANDLERS
# =====================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            details={"status_code": exc.status_code}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            details={"message": str(exc)} if settings.DEBUG else None
        ).dict()
    )


# =====================================================
# STARTUP & SHUTDOWN EVENTS
# =====================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Test connections
    try:
        supabase = get_supabase()
        logger.info("✓ Supabase connection established")

        # Test Redis connection
        from config.redis_client import get_redis
        redis = get_redis()
        redis.ping()
        logger.info("✓ Redis connection established")

    except Exception as e:
        logger.error(f"✗ Startup connection test failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info(f"Shutting down {settings.APP_NAME}")


# =====================================================
# MAIN ENTRY POINT
# =====================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,  # Changed from 8000 to avoid conflict with media_scheduler
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
