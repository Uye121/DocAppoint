import time
from django.http import JsonResponse
from django.db import connections
from django.utils import timezone

# Store startup time
STARTUP_TIME = time.time()

def health_check(request): # noqa: F401
    """Enhanced health check with startup info"""
    uptime = time.time() - STARTUP_TIME
    
    # Check database
    db_status = "healthy"
    try:
        connections['default'].cursor().execute("SELECT 1")
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return JsonResponse({
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
        "uptime_seconds": round(uptime, 2),
        "startup_complete": uptime > 10,  # Consider startup complete after 10s
        "timestamp": timezone.now().isoformat()
    })