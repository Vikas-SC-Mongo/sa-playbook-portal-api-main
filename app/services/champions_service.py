from app.core.database import db_instance
from app.aggregations.champions import champions_aggregation_pipeline
from fastapi import HTTPException
import uuid
import logging
from typing import List, Dict, Optional
import re
logger = logging.getLogger(__name__)


class ChampionsService:
    @staticmethod
    async def create_champion(champion: Dict) -> Dict:
        try:
            champion["id"] = str(uuid.uuid4())
            result = await db_instance.db.champions.insert_one(champion)
            champion["_id"] = str(result.inserted_id)
            return champion
        except Exception as e:
            logger.error("Error creating champion: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=500, detail="Failed to create champion.")

    @staticmethod
    async def get_champion_by_email(email: str) -> Optional[Dict]:
        try:
            champion = await db_instance.db.champions.find_one({"email": email})
            if champion and "_id" in champion:
                champion["_id"] = str(champion["_id"])
            return champion
        except Exception as e:
            logger.error("Error fetching champion by email: %s",
                         str(e), exc_info=True)
            raise HTTPException(
                status_code=500, detail="Failed to retrieve champion.")

    @staticmethod
    async def get_all_champions(filters: dict = {}) -> List[Dict]:
        try:
            pipeline = []
            match_conditions = []

            if filters:
                for key, value in filters.items():
                    if key.lower() == "company" and isinstance(value, list):
                        normalized = [v.lower() for v in value]

                        includes_rsi = "rsi" in normalized
                        includes_accenture = "accenture" in normalized
                        includes_capgemini = "capgemini" in normalized

                        company_filter = []

                        if includes_rsi:
                            # Exclude Accenture and/or Capgemini if not explicitly included
                            exclude_companies = []
                            if not includes_accenture:
                                exclude_companies.append(re.compile("^accenture$", re.IGNORECASE))
                            if not includes_capgemini:
                                exclude_companies.append(re.compile("^capgemini$", re.IGNORECASE))

                            if exclude_companies:
                                match_conditions.append({
                                    "company": {
                                        "$nin": exclude_companies
                                    }
                                })

                            # Include explicitly mentioned non-excluded companies
                            explicit_includes = []
                            if includes_accenture:
                                explicit_includes.append(re.compile("^accenture$", re.IGNORECASE))
                            if includes_capgemini:
                                explicit_includes.append(re.compile("^capgemini$", re.IGNORECASE))

                            match_conditions.append({
                                "$or": [
                                    {"company": {"$not": {"$in": [re.compile("^accenture$", re.IGNORECASE), re.compile("^capgemini$", re.IGNORECASE)]}}},
                                    *([{"company": regex} for regex in explicit_includes] if explicit_includes else [])
                                ]
                            })

                        else:
                            # Only direct matches (case-insensitive)
                            match_conditions.append({
                                "$or": [
                                    {"company": {"$regex": f"^{re.escape(c)}$", "$options": "i"}}
                                    for c in normalized
                                ]
                            })

                    else:
                        # Handle other fields like region, location, etc.
                        if isinstance(value, list):
                            or_conditions = [
                                {key: {
                                    "$regex": f"^{re.escape(str(v))}$", "$options": "i"}}
                                for v in value if isinstance(v, (str, int, float))
                            ]
                            if or_conditions:
                                match_conditions.append({"$or": or_conditions})
                        else:
                            if isinstance(value, (str, int, float)):
                                match_conditions.append({
                                    key: {"$regex": f"^{re.escape(str(value))}$", "$options": "i"}
                                })

            if match_conditions:
                pipeline.append({"$match": {"$and": match_conditions}})

            pipeline.extend(champions_aggregation_pipeline)

            cursor = db_instance.db.champions.aggregate(pipeline)
            champions = []
            async for champion in cursor:
                champion.pop("_id", None)
                champions.append(champion)
            return champions

        except Exception as e:
            logger.error("Error fetching champions: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to retrieve champions.")


    @staticmethod
    async def update_champion_by_id(champion_id: str, updated_data: Dict) -> Optional[Dict]:
        try:
            result = await db_instance.db.champions.update_one(
                {"id": champion_id},
                {"$set": updated_data}
            )
            if result.modified_count:
                updated_champion = await db_instance.db.champions.find_one({"id": champion_id})
                if updated_champion:
                    updated_champion["_id"] = str(updated_champion["_id"])
                return updated_champion
            return None
        except Exception as e:
            logger.error("Error updating champion: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=500, detail="Failed to update champion.")
