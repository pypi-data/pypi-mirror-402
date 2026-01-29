from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd
import io
import uuid
import os
from typing import Dict, Any, Optional
import json

from .loader import load
from .analyzer import generate_summary

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache for demo purposes
# Dictionary mapping ID -> DataFrame
data_cache: Dict[str, pd.DataFrame] = {}

def get_df(file_id: str) -> pd.DataFrame:
    if file_id not in data_cache:
        raise HTTPException(status_code=404, detail="File not found or session expired")
    return data_cache[file_id]

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    
    try:
        df = load(contents, filename=file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    
    # Generate ID
    file_id = str(uuid.uuid4())
    data_cache[file_id] = df
    
    # Analysis
    summary = generate_summary(df, file_id, file.filename)
    return summary

@app.get("/data/{file_id}")
def get_data(file_id: str, columns: Optional[str] = None, limit: int = 1000):
    df = get_df(file_id)
    
    selected_df = df
    if columns:
        cols = columns.split(',')
        # Filter valid columns
        valid_cols = [c for c in cols if c in df.columns]
        if valid_cols:
            selected_df = df[valid_cols]
            
    # Sampling / Limiting
    if len(selected_df) > limit:
        # Simple head for now, could be random sample
        # selected_df = selected_df.sample(n=limit).sort_index()
        selected_df = selected_df.head(limit)
    
    # Convert to dict records
    # Handling NaN/Infinity for JSON
    data = selected_df.replace({float('nan'): None, float('inf'): None, float('-inf'): None}).to_dict(orient='records')
    
    return {
        "data": data,
        "limit": limit,
        "total_available": len(df)
    }

# Mount static files (bundled with the package)
# Now relative to this file (server.py in plotter_core)
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
else:
    print(f"Warning: Frontend static files not found at {static_path}")
