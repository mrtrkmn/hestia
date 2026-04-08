"""IoT / automation routes.

Requirements: 10.1-10.5, 11.1-11.5
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/iot", tags=["iot"])


class AutomationRequest(BaseModel):
    name: str
    trigger_type: str
    mqtt_topic: str | None = None
    cron_expression: str | None = None
    actions: list[dict] = []
    enabled: bool = True


@router.get("/entities")
async def list_entities():
    return {"entities": []}


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    return {"entity_id": entity_id}


@router.get("/automations")
async def list_automations():
    return {"automations": []}


@router.post("/automations")
async def create_automation(req: AutomationRequest):
    return {"automation_id": "pending", "status": "created"}


@router.put("/automations/{automation_id}")
async def update_automation(automation_id: str, req: AutomationRequest):
    return {"automation_id": automation_id, "status": "updated"}


@router.delete("/automations/{automation_id}")
async def delete_automation(automation_id: str):
    return {"automation_id": automation_id, "status": "deleted"}
