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


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    project_slug: str = "default"


class PatchRequest(BaseModel):
    finding: dict
    original_code: str
    language: str = "Python"
