import pandas as pd
import io
import os
from typing import Union, Optional

def load(source: Union[str, bytes, pd.DataFrame], filename: Optional[str] = None) -> pd.DataFrame:
    """
    Loads data into a Pandas DataFrame from various sources.
    
    Args:
        source: 
            - str: Path to a local file (CSV/Excel).
            - bytes: File content in bytes.
            - pd.DataFrame: Existing DataFrame (returned as is).
        filename: Optional filename for extension detection when source is bytes.
        
    Returns:
        pd.DataFrame
    """
    try:
        # Case 1: DataFrame
        if isinstance(source, pd.DataFrame):
            return source.copy()
            
        # Case 2: File Path (str)
        if isinstance(source, str):
            if not os.path.exists(source):
                raise FileNotFoundError(f"File not found: {source}")
                
            if source.endswith('.csv'):
                return pd.read_csv(source)
            elif source.endswith(('.xls', '.xlsx')):
                return pd.read_excel(source)
            else:
                raise ValueError("Unsupported file extension. Use CSV or Excel.")

        # Case 3: Bytes
        if isinstance(source, bytes):
            if not filename:
                 raise ValueError("Filename must be provided when loading from bytes to determine format.")
                 
            if filename.endswith('.csv'):
                return pd.read_csv(io.BytesIO(source))
            elif filename.endswith(('.xls', '.xlsx')):
                return pd.read_excel(io.BytesIO(source))
            else:
                raise ValueError("Unsupported file extension. Use CSV or Excel.")
                
        raise TypeError(f"Unsupported source type: {type(source)}")

    except Exception as e:
        raise ValueError(f"Failed to load data: {str(e)}")
