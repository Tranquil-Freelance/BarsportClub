"""
Root entry point that re‑exports the FastAPI app from the backend module.
This allows uvicorn to be run from the project root as:
    uvicorn main:app --reload
"""

from backend.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)