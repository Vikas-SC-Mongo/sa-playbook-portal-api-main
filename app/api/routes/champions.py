from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import json
from app.services.champions_service import ChampionsService
router = APIRouter()


@router.post("/champions")
async def create_champion(champion: dict):
    return await ChampionsService.create_champion(champion)


@router.get("/champions/{email}")
async def get_champion(email: str):
    return await ChampionsService.get_champion_by_email(email)


@router.get("/champions")
async def get_all_champions(region: Optional[str] = Query(None),
                            company: Optional[str] = Query(None),
                            ):
    try:
        filters = {}
        if region:
            filters["region"] = json.loads(region)
        if company:
            filters["company"] = json.loads(company)
        return await ChampionsService.get_all_champions(filters)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve champions")


@router.put("/champions/{champion_id}")
async def update_champion(champion_id: str, updated_data: dict):
    updated_champion = await ChampionsService.update_champion_by_id(champion_id, updated_data)
    if updated_champion:
        return updated_champion
    else:
        raise HTTPException(status_code=404, detail="Champion not found")
