from pydantic import BaseModel, EmailStr, Field
from typing import List


# ==========================
# USER SCHEMAS
# ==========================

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ==========================
# CODE REVIEW
# ==========================

class CodeReview(BaseModel):
    code: str


# ==========================
# GITHUB REPOSITORY
# ==========================

class RepoRequest(BaseModel):
    repo_url: str


# ==========================
# REVIEW RESPONSE
# ==========================

class ReviewResponse(BaseModel):
    repository: str
    files_analyzed: int

    security_score: int
    performance_score: int
    code_quality_score: int
    overall_score: int

    issues: List[str]
    suggestions: List[str]


# ==========================
# DATABASE RESPONSE
# ==========================

class ReviewHistory(BaseModel):

    id: int
    repository: str
    files_analyzed: int

    security_score: int
    performance_score: int
    code_quality_score: int
    overall_score: int

    issues: str
    suggestions: str

    review_text: str

    class Config:
        from_attributes = True

class AIChatRequest(BaseModel):
    repo_url: str
    question: str       


class AIFixRequest(BaseModel):
    repo_url: str
    file: str
    issue: str
    line: int | None = None

class DocumentationRequest(BaseModel):
    repo_url: str
    report_type: str