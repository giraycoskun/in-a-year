from fastapi import APIRouter, File, UploadFile

router = APIRouter()


@router.post("/upload")
async def upload_github_data(file: UploadFile = File(...)):
    """Upload GitHub data export."""
    return {"message": "GitHub data upload endpoint", "filename": file.filename}


@router.get("/stats/{year}")
async def get_github_stats(year: int):
    """Get GitHub contribution stats for a specific year."""
    return {"year": year, "service": "github"}
