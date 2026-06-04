from pathlib import Path
from typing import Dict, List

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Configuration
ALLOWED_ROOT_DIR = Path("/data/logs").resolve()  # Allowed root directory


# Models
class ProcessedData(BaseModel):
    file_path: str
    rows: int
    columns: List[str]
    data: List[Dict]


@app.get("/process-csv/", response_model=ProcessedData)
async def process_csv(file_path: str):
    """
    Process a CSV file from a given path.
    - Verify that the file is in ALLOWED_ROOT_DIR.
    - Parse the CSV with pandas.
    - Return structured data.
    """
    try:
        # 1. Resolve and validate the path
        path = Path(file_path).resolve()
        if not path.is_relative_to(ALLOWED_ROOT_DIR):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied: file must be in {ALLOWED_ROOT_DIR}",
            )
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=404, detail="File not found")

        # 2. Read the CSV
        df = pd.read_csv(path)
        if df.empty:
            raise HTTPException(status_code=400, detail="Empty CSV file")

        # 3. Validate required columns
        required_columns = ["time", "voltage", "current"]
        for col in required_columns:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Missing column: {col}")

        # 4. Return the data
        return ProcessedData(
            file_path=str(path),
            rows=len(df),
            columns=list(df.columns),
            data=df.to_dict(orient="records"),
        )

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Empty CSV file")
    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail="CSV parsing error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
