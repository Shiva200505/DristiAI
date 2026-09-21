from fastapi import APIRouter, HTTPException
from backend.api.schemas import PatchApplyRequest, PatchRequest
from backend.core.patcher.apply import PatchApplyError, apply_patch
from backend.core.patcher.patch_generator import generate_patch
from backend.core.patcher.verifier import verify_patch
from backend.core.security.findings_parser import FindingSchema

router = APIRouter(prefix="/api/patches", tags=["patches"])


@router.post("/preview")
def preview_patch(payload: PatchRequest):
    finding = FindingSchema.from_dict(payload.finding)
    return generate_patch(finding, payload.original_code)


@router.post("/verify")
def verify_candidate(payload: PatchRequest):
    finding = FindingSchema.from_dict(payload.finding)
    patch = generate_patch(finding, payload.original_code)
    return verify_patch(finding, payload.original_code, patch["patched_code"], payload.language).as_dict()


@router.post("/apply")
def apply_candidate(payload: PatchApplyRequest):
    finding = FindingSchema.from_dict(payload.finding)
    verification = verify_patch(finding, payload.original_code, payload.patched_code, payload.language).as_dict()
    if verification["verification_status"] != "VERIFIED_RESOLVED":
        raise HTTPException(status_code=422, detail={"code": verification["verification_status"], "message": "Candidate patch did not pass pre-apply verification.", "verification": verification})
    try:
        result = apply_patch(payload.file_path, payload.original_code, payload.patched_code, payload.expected_sha256)
    except PatchApplyError as exc:
        raise HTTPException(status_code=409, detail={"code": "PATCH_NOT_APPLIED", "message": str(exc), "recovery": "Refresh the finding and review the current diff."}) from exc
    return {**result, "verification": verification}
