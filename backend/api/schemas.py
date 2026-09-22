from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str
    path: str
    language: str = "Python"


class ScanRequest(BaseModel):
    file_path: str = "untitled.py"
    language: str = "Python"
    code_content: str = Field(min_length=1, max_length=200_000)
    triggered_by: str = "manual"
    project_root: str | None = None


class ProjectScanRequest(BaseModel):
    project_root: str
    changed_files: list[str] = Field(default_factory=list)
    triggered_by: str = "project"
    use_external_tools: bool = True


class DependencyScanRequest(BaseModel):
    project_root: str
    allow_network: bool = False


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    project_slug: str = "default"


class ExplainRequest(BaseModel):
    code_context: str = Field(default="", max_length=100_000)
    rag_context: str = Field(default="", max_length=100_000)


class PatchRequest(BaseModel):
    finding: dict
    original_code: str = Field(max_length=200_000)
    language: str = "Python"


class PatchApplyRequest(PatchRequest):
    file_path: str
    patched_code: str = Field(max_length=200_000)
    expected_sha256: str | None = None
    project_root: str | None = None
