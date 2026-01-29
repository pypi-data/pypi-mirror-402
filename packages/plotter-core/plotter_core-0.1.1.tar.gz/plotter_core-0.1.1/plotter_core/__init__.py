from .loader import load
from .analyzer import generate_summary

def run_ui(host="127.0.0.1", port=8000):
    """
    Launches the Plotter UI server.
    """
    import uvicorn
    import os
    
    # We need to run the app located in plotter_core.server
    # Using module string allows reloading if needed, but for lib usage instance is fine usually.
    # However, relative imports in server.py might be tricky if not run as module.
    # Let's run it as a uvicorn app string if possible, or pass the app instance.
    
    from .server import app
    print(f"Starting Plotter UI at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
