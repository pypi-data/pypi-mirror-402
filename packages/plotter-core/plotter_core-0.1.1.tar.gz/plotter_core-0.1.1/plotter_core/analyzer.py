import pandas as pd
from typing import Dict, Any, List

def generate_summary(df: pd.DataFrame, file_id: str, filename: str) -> Dict[str, Any]:
    """
    Generates a summary of the DataFrame including column types, null usage, and examples.
    """
    summary = {
        "file_id": file_id,
        "filename": filename,
        "total_rows": len(df),
        "columns": []
    }
    
    for col in df.columns:
        col_data = df[col]
        dtype = str(col_data.dtype)
        null_count = int(col_data.isnull().sum())
        null_percentage = round((null_count / len(df)) * 100, 2)
        # Get 3 non-null example values
        examples = col_data.dropna().head(3).tolist()
        
        summary["columns"].append({
            "name": col,
            "type": dtype,
            "null_count": null_count,
            "null_percentage": null_percentage,
            "examples": examples,
            "is_numeric": bool(pd.api.types.is_numeric_dtype(col_data))
        })
        
    return summary
