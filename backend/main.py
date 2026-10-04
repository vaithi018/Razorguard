import os
import sys

# Ensure backend directory is on sys.path for Vercel Serverless / Service runtime
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from app.main import app
except Exception as e:
    import traceback
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    err_trace = traceback.format_exc()
    print("FATAL ERROR IMPORTING app.main:", err_trace, file=sys.stderr)

    # Diagnostic app to display exact error rather than opaque FUNCTION_INVOCATION_FAILED
    app = FastAPI(title="RazorGuard Startup Diagnostic")

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    async def diagnostic_handler(full_path: str):
        return JSONResponse(
            status_code=500,
            content={
                "status": "startup_failed",
                "error": str(e),
                "traceback": err_trace.splitlines(),
            }
        )

__all__ = ["app"]
