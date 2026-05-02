"""Populate the Atlas `skills` collection with starter coordination protocols.

Run once after the vector index is built:

    uv run python seed_skills.py

Idempotent: skills are upserted by `id`.
"""

import asyncio
from datetime import datetime, timezone

from memory.client import get_collection, ping
from memory.search import embed_document
from schemas.skill import Skill

SEED_SKILLS = [
    {
        "id": "PT-0001",
        "name": "Discharge chain coordination",
        "description": (
            "Discharge has been signed for a patient. Coordinate pharmacy for take-home "
            "medication, porter for transport off the ward, cleaner for the bay, and bed "
            "manager for the new allocation. Track each confirmation, escalate after 20 minutes."
        ),
        "trigger_conditions": ["discharge", "pharmacy", "porter", "bed", "ward"],
        "code": (
            "async def coordinate(patient_id, ward, **kwargs):\n"
            "    steps = [\n"
            "        {'role': 'pharmacy', 'message': f'Discharge meds ready for {patient_id} on {ward}', 'channel': 'bleep'},\n"
            "        {'role': 'porter', 'message': f'Patient {patient_id} ready for transport from {ward}', 'channel': 'app'},\n"
            "        {'role': 'cleaner', 'message': f'Bay free in {ward} after {patient_id} discharge', 'channel': 'app'},\n"
            "        {'role': 'bed_manager', 'message': f'Bed available in {ward}', 'channel': 'app'},\n"
            "    ]\n"
            "    return {\n"
            "        'steps_initiated': steps,\n"
            "        'expected_confirmations': ['pharmacy', 'porter', 'cleaner', 'bed_manager'],\n"
            "        'escalation_after_minutes': 20,\n"
            "        'protocol_summary': 'Discharge chain initiated.',\n"
            "    }\n"
        ),
    },
    {
        "id": "PT-0002",
        "name": "Missing specimen trace",
        "description": (
            "A blood or tissue specimen was drawn on a ward but the lab has no record of receipt. "
            "Trace each logged handoff, identify the break in the chain, route a task to the "
            "nearest staff member to physically check the location."
        ),
        "trigger_conditions": ["specimen", "blood", "lab", "missing", "trace"],
        "code": (
            "async def coordinate(patient_id, ward, **kwargs):\n"
            "    steps = [\n"
            "        {'role': 'lab', 'message': f'Confirm receipt status for {patient_id} sample', 'channel': 'bleep'},\n"
            "        {'role': 'phlebotomy', 'message': f'Confirm draw time for {patient_id}', 'channel': 'app'},\n"
            "        {'role': 'ward_nurse', 'message': f'Physical check fridge in {ward} for {patient_id}', 'channel': 'app'},\n"
            "    ]\n"
            "    return {\n"
            "        'steps_initiated': steps,\n"
            "        'expected_confirmations': ['lab', 'phlebotomy', 'ward_nurse'],\n"
            "        'escalation_after_minutes': 15,\n"
            "        'protocol_summary': 'Specimen trace initiated across lab, phlebotomy, and ward.',\n"
            "    }\n"
        ),
    },
    {
        "id": "PT-0003",
        "name": "Shift handover gap",
        "description": (
            "End of shift in 20 minutes. Cross-check open tasks per bed against documented "
            "handover. For each undocumented open task, send a targeted message to the outgoing "
            "and incoming nurse identifying the bed and the pending action."
        ),
        "trigger_conditions": ["shift", "handover", "outstanding", "tasks", "ward"],
        "code": (
            "async def coordinate(patient_id, ward, **kwargs):\n"
            "    steps = [\n"
            "        {'role': 'outgoing_nurse', 'message': f'Document outstanding tasks in {ward}', 'channel': 'app'},\n"
            "        {'role': 'incoming_nurse', 'message': f'Pending tasks brief for {ward}', 'channel': 'app'},\n"
            "        {'role': 'coordinator', 'message': f'Verify handover completeness for {ward}', 'channel': 'dashboard'},\n"
            "    ]\n"
            "    return {\n"
            "        'steps_initiated': steps,\n"
            "        'expected_confirmations': ['outgoing_nurse', 'incoming_nurse'],\n"
            "        'escalation_after_minutes': 10,\n"
            "        'protocol_summary': 'Shift handover gap check initiated.',\n"
            "    }\n"
        ),
    },
    {
        "id": "PT-0004",
        "name": "Pre-op checklist completion",
        "description": (
            "Surgery scheduled in approximately two hours. Verify consent signed, "
            "anaesthetic review complete, blood sample sent. For any missing item, simultaneously "
            "page the responsible role rather than sequentially."
        ),
        "trigger_conditions": ["surgery", "preop", "consent", "anaesthetic", "checklist"],
        "code": (
            "async def coordinate(patient_id, ward, **kwargs):\n"
            "    steps = [\n"
            "        {'role': 'anaesthetics', 'message': f'Pre-op review needed for {patient_id}', 'channel': 'bleep'},\n"
            "        {'role': 'ward_nurse', 'message': f'Confirm bloods sent for {patient_id}', 'channel': 'app'},\n"
            "        {'role': 'surgeon', 'message': f'Confirm consent signed for {patient_id}', 'channel': 'app'},\n"
            "    ]\n"
            "    return {\n"
            "        'steps_initiated': steps,\n"
            "        'expected_confirmations': ['anaesthetics', 'ward_nurse', 'surgeon'],\n"
            "        'escalation_after_minutes': 30,\n"
            "        'protocol_summary': 'Pre-op checklist verification initiated in parallel.',\n"
            "    }\n"
        ),
    },
    {
        "id": "PT-0005",
        "name": "Equipment trace and retrieval",
        "description": (
            "A piece of mobile equipment (IV pump, ECG, ultrasound) was last logged on one ward "
            "and is needed urgently on another. Trace its last logged location, send a retrieval "
            "request to the nearest staff member, initiate transport to the requesting ward."
        ),
        "trigger_conditions": ["equipment", "pump", "trace", "retrieval", "ward"],
        "code": (
            "async def coordinate(patient_id, ward, **kwargs):\n"
            "    last_seen = kwargs.get('last_seen_ward', 'unknown')\n"
            "    steps = [\n"
            "        {'role': 'equipment_log', 'message': f'Locate equipment last seen in {last_seen}', 'channel': 'app'},\n"
            "        {'role': 'nearest_porter', 'message': f'Retrieve equipment from {last_seen} to {ward}', 'channel': 'app'},\n"
            "        {'role': 'ward_clerk', 'message': f'Confirm receipt on {ward}', 'channel': 'dashboard'},\n"
            "    ]\n"
            "    return {\n"
            "        'steps_initiated': steps,\n"
            "        'expected_confirmations': ['equipment_log', 'nearest_porter', 'ward_clerk'],\n"
            "        'escalation_after_minutes': 15,\n"
            "        'protocol_summary': 'Equipment trace and retrieval initiated.',\n"
            "    }\n"
        ),
    },
]


async def main() -> None:
    if not await ping():
        raise SystemExit("Cannot reach MongoDB Atlas — check MONGODB_URI in .env")

    collection = get_collection("skills")
    print(f"Seeding {len(SEED_SKILLS)} skills...")

    for raw in SEED_SKILLS:
        embedding = await embed_document(raw["description"])
        skill = Skill(
            id=raw["id"],
            name=raw["name"],
            description=raw["description"],
            code=raw["code"],
            embedding=embedding,
            trigger_conditions=raw["trigger_conditions"],
            validation_score=1.0,
            usage_count=0,
            created_at=datetime.now(timezone.utc),
            trust_origin="MediMind-seed",
        )
        await collection.update_one(
            {"id": skill.id},
            {"$set": skill.to_dict()},
            upsert=True,
        )
        print(f"  upserted {skill.id} — {skill.name}")

    total = await collection.count_documents({})
    print(f"Done. Total skills in Atlas: {total}")


if __name__ == "__main__":
    asyncio.run(main())
