from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi import Request
from typing import Dict
import os
from app.services.certification_review_service import convert_to_md
from app.services.certification_review_service import evaluate_submission

router = APIRouter()


@router.post("/certification-review")
async def certification_review(request: Request, pdf: UploadFile = File(...)) -> Dict[str, str]:
    try:
        # Validate file type
        if pdf.content_type != "application/pdf":
            raise HTTPException(
                status_code=400, detail="Invalid file type. Only PDF files are allowed.")

        # Save the uploaded file
        file_path = pdf.filename
        with open(file_path, "wb") as buffer:
            buffer.write(await pdf.read())

        # Process the PDF
        md_text = convert_to_md(file_path)

        system_output = evaluate_submission(md_text)

        # Prepare the response
        res = {"status": "Success", "message": system_output}

        return res

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return {"status": "Error", "message": error_message}
    finally:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
