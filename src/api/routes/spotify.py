from fastapi import APIRouter, File, UploadFile

router = APIRouter()


@router.post("/upload")
async def upload_spotify_data(file: UploadFile = File(...)):
    """Upload Spotify extended streaming history JSON file."""
    return {"message": "Spotify data upload endpoint", "filename": file.filename}


@router.get("/stats/{year}")
async def get_spotify_stats(year: int):
    """Get Spotify listening stats for a specific year."""
    return {"year": year, "service": "spotify"}
