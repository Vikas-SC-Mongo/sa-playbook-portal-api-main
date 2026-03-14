from app.core.database import db_instance
from fastapi import HTTPException
from datetime import datetime


class FeedbackService:

    @staticmethod
    async def submit_feedback(feedback: dict):
        try:
            feedback_data = feedback
            feedback_data["createdAt"] = datetime.utcnow()
            await db_instance.db.feedback.insert_one(feedback_data)
            return {"message": "Feedback submitted!"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def get_all_feedbacks():
        try:
            feedbacks = []
            async for fb in db_instance.db.feedback.find().sort("createdAt", -1):
                feedbacks.append({
                    "_id": str(fb["_id"]),
                    "name": fb["name"],
                    "feedback": fb["feedback"],
                    "pageName": fb["pageName"],
                    "createdAt": fb["createdAt"]
                })
            return feedbacks
        except Exception as e:
            raise RuntimeError(f"Error fetching uploaded files: {str(e)}")
