from fastapi import APIRouter, File, UploadFile

router = APIRouter()


@router.post("/upload")
async def upload_trakt_data(file: UploadFile = File(...)):
    """Upload Trakt watching history export."""
    return {"message": "Trakt data upload endpoint", "filename": file.filename}


@router.get("/stats/{year}")
async def get_trakt_stats(year: int):
    """Get movies/TV watching stats for a specific year."""
    return {"year": year, "service": "trakt"}
