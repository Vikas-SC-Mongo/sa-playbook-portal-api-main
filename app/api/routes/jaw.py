from fastapi import APIRouter, Query, HTTPException, Body
from app.services.jaw_service import JAWService
from typing import Optional

router = APIRouter()


@router.post("/upload/jaw")
async def jaw_file_data(file_data: dict):
    file_id = await JAWService.jaw_file_metadata(file_data["filename"])
    await JAWService.jaw_file_data(file_id, file_data["data"])
    return {"message": "File uploaded successfully", "file_id": file_id}


@router.get("/jaw-files")
async def get_jaw_files(month: Optional[int] = Query(None, ge=1, le=12),):
    return await JAWService.get_jaw_files(month)


@router.get("/jaw-files/{file_id}")
async def get_jaw_file_data(file_id: str):
    file_data = await JAWService.get_jaw_file_data(file_id)
    if file_data:
        return file_data
    raise HTTPException(status_code=404, detail="File not found")


@router.post("/log-dr-download")
async def log_download(meta: dict = Body(...)):
    inserted_id = await JAWService.log_design_review_document_download(meta)
    return {"status": "success", "id": inserted_id}


@router.get("/design-review/downloads/stats")
async def download_stats(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=1900)
):
    if not month and not year:
        raise HTTPException(
            status_code=400, detail="Provide at least 'month' or 'year'")

    downloadedDRs = await JAWService.get_total_dr_downloads(month, year)
    return {
        "downloadedDRs": downloadedDRs["downloadedDRs"],
        "totalDownloads": downloadedDRs["total"],
        "filters": {
            "month": month,
            "year": year
        }
    }
