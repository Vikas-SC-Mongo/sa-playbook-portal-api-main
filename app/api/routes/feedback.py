from fastapi import APIRouter
from app.services.feedback_service import FeedbackService

router = APIRouter()

@router.post("/feedback")
async def submit_feedback(feedback: dict):
    return await FeedbackService.submit_feedback(feedback)

@router.get("/feedbacks")
async def get_all_feedbacks():
    return await FeedbackService.get_all_feedbacks()