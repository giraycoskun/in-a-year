from fastapi import APIRouter, File, UploadFile

router = APIRouter()


@router.post("/upload")
async def upload_hardcover_data(file: UploadFile = File(...)):
    """Upload Hardcover reading data export."""
    return {"message": "Hardcover data upload endpoint", "filename": file.filename}


@router.get("/stats/{year}")
async def get_hardcover_stats(year: int):
    """Get reading stats for a specific year."""
    return {"year": year, "service": "hardcover"}
