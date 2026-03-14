from fastapi import HTTPException
from app.core.database import db_instance
from bson import ObjectId
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class JAWService:

    @staticmethod
    async def jaw_file_metadata(filename: str) -> str:
        db = db_instance.db
        file_metadata = {
            "filename": filename,
            "created_at": datetime.utcnow()
        }
        try:
            result = await db.jaw_files.insert_one(file_metadata)
            return str(result.inserted_id)
        except Exception as e:
            raise RuntimeError(f"Error storing file metadata: {str(e)}")

    @staticmethod
    async def jaw_file_data(file_id: str, data: List[Dict]) -> None:
        db = db_instance.db
        file_data_record = {
            "file_id": ObjectId(file_id),  # Reference to `jaw_files`
            "data": data
        }
        try:
            await db.jaw_details.insert_one(file_data_record)
        except Exception as e:
            raise RuntimeError(f"Error storing file data: {str(e)}")

    @staticmethod
    async def get_jaw_files(month: Optional[int] = None) -> List[Dict]:
        try:
            db = db_instance.db
            collection = db.jaw_files

            query = {}

            if month:
                current_year = datetime.utcnow().year
                start_date = datetime(current_year, month, 1)
                end_date = (
                    datetime(current_year + 1, 1, 1)
                    if month == 12 else
                    datetime(current_year, month + 1, 1)
                )
                query["created_at"] = {"$gte": start_date, "$lt": end_date}

            files_cursor = collection.find(
                query,
                {"_id": 1, "filename": 1, "created_at": 1}
            )
            files = await files_cursor.to_list(length=None)

            return [
                {
                    "_id": str(f["_id"]),
                    "filename": f["filename"],
                    "created_at": f["created_at"]
                }
                for f in files
            ]
        except Exception as e:
            raise RuntimeError(f"Error fetching uploaded files: {str(e)}")

    @staticmethod
    async def get_jaw_file_data(file_id: str) -> Optional[List[Dict]]:
        try:
            db = db_instance.db
            file_data = await db.jaw_details.find_one(
                {"file_id": ObjectId(file_id)},
                {"_id": 0, "data": 1}
            )
            return file_data["data"] if file_data else None
        except Exception as e:
            raise RuntimeError(f"Error fetching file content: {str(e)}")

    @staticmethod
    async def setup_jaw_indexes():
        db = db_instance.db
        await db.jaw_files.create_index("filename", unique=True)

        await db.jaw_files.create_index("created_at")

        await db.jaw_details.create_index("file_id")

    @staticmethod
    async def log_design_review_document_download(meta: dict) -> str:
        if not meta or not isinstance(meta, dict):
            logger.error("Invalid metadata provided for download logging")
            raise ValueError("Metadata must be a non-empty dictionary")

        try:
            if "download_time" not in meta:
                meta["download_time"] = datetime.utcnow()

            db = db_instance.db

            result = await db.dr_downloads.insert_one(meta)

            logger.info(
                f"Logged DR document download with ID: {result.inserted_id}")

            application_id = meta.get("applicationId")
            if application_id:
                update_result = await db.jaw_details.update_one(
                    {"data.applicationId": application_id},
                    {
                        "$set": {
                            "data.$[elem].is_design_review_downloaded": True
                        }
                    },
                    array_filters=[{"elem.applicationId": application_id}]
                )

                if update_result.modified_count > 0:
                    logger.info(
                        f"Marked applicationId '{application_id}' as downloaded in jaw_details")
                else:
                    logger.warning(
                        f"No matching applicationId '{application_id}' found in jaw_details")

            return str(result.inserted_id)

        except Exception as e:
            logger.error(
                f"Failed to log DR document download: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to log document download. Please try again later."
            ) from e

    @staticmethod
    async def get_total_dr_downloads(month: Optional[int] = None, year: Optional[int] = None) -> int:
        if month is not None and (month < 1 or month > 12):
            raise ValueError("Month must be between 1 and 12")

        if year is not None and year < 2000:
            raise ValueError("Year must be 2000 or later")

        try:
            db = db_instance.db
            query = {}

            if month is not None:
                query["created_month"] = month
            if year is not None:
                query["created_year"] = year

            documents_cursor = db.dr_downloads.find(query, {"_id": 0})
            downloadedDRs = await documents_cursor.to_list(length=None)
            total = len(downloadedDRs)

            logger.debug(
                f"DR downloads count query: {query}, result: {downloadedDRs}")

            return {
                "total": total,
                "downloadedDRs": downloadedDRs
            }

        except Exception as e:
            logger.error(
                f"Failed to get DR downloads count: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve download statistics. Please try again later."
            ) from e
