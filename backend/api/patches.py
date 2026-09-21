from fastapi import APIRouter
from backend.api.schemas import PatchRequest
from backend.core.patcher.patch_generator import generate_patch
from backend.core.patcher.verifier import verify_patch
from backend.core.security.findings_parser import FindingSchema

router = APIRouter(prefix="/api/patches", tags=["patches"])


@router.post("/preview")
def preview_patch(payload: PatchRequest):
    finding = FindingSchema(**payload.finding)
    return generate_patch(finding, payload.original_code)


@router.post("/verify")
def verify_candidate(payload: PatchRequest):
    finding = FindingSchema(**payload.finding)
    patch = generate_patch(finding, payload.original_code)
    return verify_patch(finding, payload.original_code, patch["patched_code"], payload.language).as_dict()
