import os
import json
import tempfile
import requests

from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from fastapi import (
    FastAPI,
    Depends,
    HTTPException
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from pydantic import BaseModel

from app.database import (
    engine,
    Base,
    get_db
)

from app.models import (
    User,
    Review
)

from app.schemas import (
    UserCreate,
    UserLogin,
    CodeReview,
    RepoRequest,
    AIChatRequest,
    AIFixRequest
)

from app.auth import (
    hash_password,
    verify_password
)

from services.ai_chat import AIChatService
from services.ai_fix import AIFixService
from services.documentation import DocumentationService


# ==========================================================
# LOAD ENVIRONMENT FIRST
# ==========================================================

env_path = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / ".env"
)

load_dotenv(
    dotenv_path=env_path
)


# ==========================================================
# GROQ
# ==========================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

if not GROQ_API_KEY:

    raise RuntimeError(
        "GROQ_API_KEY not found in .env"
    )


client = Groq(
    api_key=GROQ_API_KEY
)


# ==========================================================
# SERVICES
# ==========================================================

documentation_service = DocumentationService()

ai_fix_service = AIFixService()

ai_chat_service = AIChatService()


# ==========================================================
# GITHUB
# ==========================================================

GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN"
)


GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json"
}


if GITHUB_TOKEN:

    GITHUB_HEADERS[
        "Authorization"
    ] = f"Bearer {GITHUB_TOKEN}"


github_session = requests.Session()

github_session.headers.update(
    GITHUB_HEADERS
)


# ==========================================================
# DATABASE
# ==========================================================

Base.metadata.create_all(
    bind=engine
)


# ==========================================================
# FASTAPI
# ==========================================================

app = FastAPI(
    title="Code Sage AI",
    version="1.0.0"
)


# ==========================================================
# CORS
# ==========================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ==========================================================
# SUPPORTED FILES
# ==========================================================

SUPPORTED_EXTENSIONS = (

    ".py",

    ".js",

    ".ts",

    ".java",

    ".cpp",

    ".c",

    ".cs",

    ".go",

    ".php",

    ".rs"
)


IGNORED_DIR_NAMES = (

    "node_modules",

    ".git",

    "__pycache__",

    "venv",

    ".venv",

    "dist",

    "build"
)


# ==========================================================
# GITHUB ERRORS
# ==========================================================

class GithubRateLimitError(Exception):

    pass


class GithubNotFoundError(Exception):

    pass


# ==========================================================
# GITHUB RESPONSE CHECK
# ==========================================================

def _check_github_response(
    response
):

    if response.status_code == 404:

        raise GithubNotFoundError(

            "Repository not found. "
            "Check the URL and make sure it is public."

        )


    if (

        response.status_code == 403

        and

        response.headers.get(
            "X-RateLimit-Remaining"
        ) == "0"

    ):

        raise GithubRateLimitError(

            "GitHub API rate limit reached. "
            "Add a GITHUB_TOKEN to your .env "
            "or wait for the limit to reset."

        )


# ==========================================================
# GET DEFAULT BRANCH
# ==========================================================

def get_default_branch(
    owner: str,
    repo: str
) -> str:

    response = github_session.get(

        f"https://api.github.com/repos/"
        f"{owner}/{repo}",

        timeout=10

    )

    _check_github_response(
        response
    )


    if response.status_code != 200:

        raise GithubNotFoundError(

            "Could not read repository metadata."

        )


    return response.json()[
        "default_branch"
    ]


# ==========================================================
# IGNORED PATH
# ==========================================================

def is_ignored_path(
    path: str
) -> bool:

    parts = path.split("/")

    return any(

        part in IGNORED_DIR_NAMES

        for part in parts

    )


# ==========================================================
# GET CODE FILES
# ==========================================================

def get_code_files(
    owner: str,
    repo: str,
    branch: str
):

    response = github_session.get(

        f"https://api.github.com/repos/"
        f"{owner}/{repo}/git/trees/{branch}",

        params={
            "recursive": "1"
        },

        timeout=15

    )

    _check_github_response(
        response
    )


    if response.status_code != 200:

        return []


    tree = response.json().get(
        "tree",
        []
    )


    files = []


    for item in tree:

        if item.get(
            "type"
        ) != "blob":

            continue


        path = item.get(
            "path",
            ""
        )


        if is_ignored_path(
            path
        ):

            continue


        if path.endswith(
            SUPPORTED_EXTENSIONS
        ):

            raw_url = (

                "https://raw.githubusercontent.com/"

                f"{owner}/"

                f"{repo}/"

                f"{branch}/"

                f"{path}"

            )

            files.append(
                raw_url
            )


    return files


# ==========================================================
# RELATIVE PATHS
#
# Converts raw.githubusercontent.com URLs back into clean
# relative file paths, e.g. "app/main.py", so the frontend
# can show a readable file list / dropdown.
# ==========================================================

def to_relative_paths(
    code_files,
    owner: str,
    repo: str,
    branch: str
):

    prefix = (
        "https://raw.githubusercontent.com/"
        f"{owner}/{repo}/{branch}/"
    )

    return [
        url.replace(prefix, "")
        for url in code_files
    ]


# ==========================================================
# HOME
# ==========================================================

@app.get("/")
def home():

    return {

        "message":
        "Code Sage AI Backend Running"

    }


# ==========================================================
# REGISTER
# ==========================================================

@app.post("/register")
def register(

    user: UserCreate,

    db: Session = Depends(
        get_db
    )

):

    existing = (

        db.query(User)

        .filter(
            User.email == user.email
        )

        .first()

    )


    if existing:

        raise HTTPException(

            status_code=400,

            detail="Email already registered"

        )


    new_user = User(

        name=user.name,

        email=user.email,

        password=hash_password(
            user.password
        )

    )


    db.add(
        new_user
    )

    db.commit()

    db.refresh(
        new_user
    )


    return {

        "message":
        "User registered successfully",

        "user": {

            "id": new_user.id,

            "name": new_user.name,

            "email": new_user.email

        }

    }


# ==========================================================
# LOGIN
# ==========================================================

@app.post("/login")
def login(

    user: UserLogin,

    db: Session = Depends(
        get_db
    )

):

    db_user = (

        db.query(User)

        .filter(
            User.email == user.email
        )

        .first()

    )


    if not db_user:

        raise HTTPException(

            status_code=404,

            detail="User not found"

        )


    if not verify_password(

        user.password,

        db_user.password

    ):

        raise HTTPException(

            status_code=401,

            detail="Invalid password"

        )


    return {

        "message":
        "Login successful",

        "user": {

            "id": db_user.id,

            "name": db_user.name,

            "email": db_user.email

        }

    }


# ==========================================================
# RULE BASED REVIEW
# ==========================================================

@app.post("/review")
def review_code(
    data: CodeReview
):

    code = data.code

    issues = []


    if (
        "password =" in code
        or
        "password=" in code
    ):

        issues.append(
            "Hardcoded password detected"
        )


    if (
        "api_key =" in code
        or
        "secret =" in code
    ):

        issues.append(
            "Hardcoded API key or secret detected"
        )


    if "SELECT *" in code.upper():

        issues.append(
            "Avoid using SELECT * in SQL queries"
        )


    if "print(" in code:

        issues.append(
            "Debug print statement found"
        )


    if "except:" in code:

        issues.append(
            "Avoid using bare except statements"
        )


    if len(issues) == 0:

        issues.append(
            "No obvious issues found"
        )


    return {

        "issues": issues

    }


# ==========================================================
# AI REVIEW
# ==========================================================

@app.post("/ai-review")
def ai_review(
    data: CodeReview
):

    prompt = f"""

You are a Senior Software Engineer.

Review this code.

Find:

1. Bugs
2. Security Issues
3. Performance Problems
4. Code Quality Issues
5. Suggestions

Return the answer in Markdown.

Code:

{data.code}

"""


    response = client.chat.completions.create(

        model=os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        ),

        temperature=0.2,

        messages=[

            {

                "role": "user",

                "content": prompt

            }

        ]

    )


    return {

        "review":
        response.choices[0].message.content

    }


# ==========================================================
# JSON CLEANER
# ==========================================================

def clean_json(
    text: str
):

    text = text.strip()


    if text.startswith(
        "```json"
    ):

        text = text.replace(
            "```json",
            "",
            1
        )


    if text.startswith(
        "```"
    ):

        text = text.replace(
            "```",
            "",
            1
        )


    if text.endswith(
        "```"
    ):

        text = text[:-3]


    return text.strip()


# ==========================================================
# ANALYZE GITHUB REPOSITORY
# ==========================================================

@app.post("/analyze-repo")
def analyze_repo(

    data: RepoRequest,

    db: Session = Depends(
        get_db
    )

):

    try:

        repo_url = data.repo_url.strip()

        parts = (
            repo_url
            .rstrip("/")
            .split("/")
        )


        if len(parts) < 5:

            raise HTTPException(

                status_code=400,

                detail=
                "Invalid GitHub Repository URL"

            )


        owner = parts[-2]

        repo = parts[-1]


        try:

            branch = get_default_branch(

                owner,
                repo

            )


            code_files = get_code_files(

                owner,
                repo,
                branch

            )


        except GithubRateLimitError as e:

            raise HTTPException(

                status_code=429,

                detail=str(e)

            )


        except GithubNotFoundError as e:

            raise HTTPException(

                status_code=404,

                detail=str(e)

            )


        if not code_files:

            raise HTTPException(

                status_code=404,

                detail=
                "No supported source files found."

            )


        # ==================================================
        # Relative file paths for the frontend (Auto Fix
        # dropdown, etc.)
        # ==================================================

        file_list = to_relative_paths(
            code_files,
            owner,
            repo,
            branch
        )


        code_content = ""

        files_read = 0


        for file_url in code_files:

            if files_read >= 15:

                break


            try:

                raw = requests.get(

                    file_url,

                    timeout=10

                )


                if raw.status_code == 200:

                    code_content += (

                        "\n\n"
                        "========== FILE ==========\n\n"

                    )

                    code_content += (

                        file_url
                        + "\n\n"

                    )

                    code_content += (
                        raw.text[:3000]
                    )

                    files_read += 1


            except Exception:

                continue


        if not code_content:

            raise HTTPException(

                status_code=500,

                detail=
                "Unable to download repository code."

            )


        prompt = f"""

You are an expert Senior Software Engineer.

Review the repository.

Return ONLY valid JSON.

Do NOT write markdown.

Do NOT use ```json.

JSON Format:

{{
    "security_score": 0,
    "performance_score": 0,
    "code_quality_score": 0,
    "overall_score": 0,
    "issues": [
        "Issue 1"
    ],
    "suggestions": [
        "Suggestion 1"
    ]
}}

Repository Code:

{code_content}

"""


        ai_response = client.chat.completions.create(

            model=os.getenv(
                "GROQ_MODEL",
                "openai/gpt-oss-120b"
            ),

            temperature=0.1,

            messages=[

                {

                    "role": "user",

                    "content": prompt

                }

            ]

        )


        raw_output = (
            ai_response
            .choices[0]
            .message
            .content
        )


        raw_output = clean_json(
            raw_output
        )


        result = json.loads(
            raw_output
        )


        new_review = Review(

            repository=repo,

            files_analyzed=files_read,

            security_score=result[
                "security_score"
            ],

            performance_score=result[
                "performance_score"
            ],

            code_quality_score=result[
                "code_quality_score"
            ],

            overall_score=result[
                "overall_score"
            ],

            issues=json.dumps(
                result["issues"]
            ),

            suggestions=json.dumps(
                result["suggestions"]
            ),

            review_text=raw_output

        )


        db.add(
            new_review
        )

        db.commit()

        db.refresh(
            new_review
        )


        return {

            "repository": repo,

            "files_analyzed": files_read,

            "security_score":
            result["security_score"],

            "performance_score":
            result["performance_score"],

            "code_quality_score":
            result["code_quality_score"],

            "overall_score":
            result["overall_score"],

            "issues":
            result["issues"],

            "suggestions":
            result["suggestions"],

            "file_list": file_list

        }


    except json.JSONDecodeError:

        raise HTTPException(

            status_code=500,

            detail=
            "AI returned invalid JSON."

        )


    except HTTPException:

        raise


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )


# ==========================================================
# AI DEVELOPER CHAT
# ==========================================================

@app.post("/ai-chat")
def ai_chat(
    data: AIChatRequest
):

    try:

        repo_url = data.repo_url.strip()

        question = data.question.strip()


        if not question:

            raise HTTPException(

                status_code=400,

                detail=
                "Question cannot be empty."

            )


        parts = (
            repo_url
            .rstrip("/")
            .split("/")
        )


        if len(parts) < 5:

            raise HTTPException(

                status_code=400,

                detail=
                "Invalid GitHub Repository URL"

            )


        owner = parts[-2]

        repo = parts[-1]


        try:

            branch = get_default_branch(

                owner,
                repo

            )


            code_files = get_code_files(

                owner,
                repo,
                branch

            )


        except GithubRateLimitError as e:

            raise HTTPException(

                status_code=429,

                detail=str(e)

            )


        except GithubNotFoundError as e:

            raise HTTPException(

                status_code=404,

                detail=str(e)

            )


        if not code_files:

            raise HTTPException(

                status_code=404,

                detail=
                "No supported source files found."

            )


        files = []


        for file_url in code_files[:5]:

            try:

                raw = requests.get(

                    file_url,

                    timeout=10

                )


                if raw.status_code != 200:

                    continue


                files.append({

                    "path": file_url,

                    "content": raw.text[:1500]

                })


            except Exception:

                continue


        if not files:

            raise HTTPException(

                status_code=500,

                detail=
                "Unable to download repository code."

            )


        repository = {

            "owner": owner,

            "repository": repo,

            "branch": branch,

            "language": "Unknown",

            "files": files

        }


        result = ai_chat_service.ask(

            question=question,

            repository=repository

        )


        return {

            "success": True,

            "repository":
            f"{owner}/{repo}",

            "branch": branch,

            "files_analyzed":
            len(files),

            "question": question,

            "answer":
            result["answer"],

            "model":
            result["model"]

        }


    except HTTPException:

        raise


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )


# ==========================================================
# AI AUTO FIX
# ==========================================================

@app.post("/ai-fix")
def ai_fix(
    data: AIFixRequest
):

    try:

        repo_url = data.repo_url.strip()


        parts = (
            repo_url
            .rstrip("/")
            .split("/")
        )


        if len(parts) < 5:

            raise HTTPException(

                status_code=400,

                detail=
                "Invalid GitHub Repository URL"

            )


        owner = parts[-2]

        repo = parts[-1]


        try:

            branch = get_default_branch(

                owner,
                repo

            )


            code_files = get_code_files(

                owner,
                repo,
                branch

            )


        except GithubRateLimitError as e:

            raise HTTPException(

                status_code=429,

                detail=str(e)

            )


        except GithubNotFoundError as e:

            raise HTTPException(

                status_code=404,

                detail=str(e)

            )


        target_file = None


        for file_url in code_files:

            if data.file in file_url:

                target_file = file_url

                break


        if not target_file:

            raise HTTPException(

                status_code=404,

                detail=
                f"File not found: {data.file}"

            )


        raw = requests.get(

            target_file,

            timeout=10

        )


        if raw.status_code != 200:

            raise HTTPException(

                status_code=500,

                detail=
                "Unable to retrieve source file."

            )


        code = raw.text


        result = ai_fix_service.generate_fix(

            file_path=data.file,

            code=code,

            issue=data.issue,

            line=data.line

        )


        return {

            "success": True,

            "repository":
            f"{owner}/{repo}",

            "branch": branch,

            "file": data.file,

            "issue": data.issue,

            "original_code":
            result.get(
                "original_code",
                ""
            ),

            "fixed_code":
            result.get(
                "fixed_code",
                ""
            ),

            "explanation":
            result.get(
                "explanation",
                ""
            ),

            "changes":
            result.get(
                "changes",
                []
            ),

            "model":
            ai_fix_service.model

        }


    except HTTPException:

        raise


    except json.JSONDecodeError:

        raise HTTPException(

            status_code=500,

            detail=
            "AI returned invalid JSON."

        )


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )


# ==========================================================
# REVIEW HISTORY
# ==========================================================

@app.get("/reviews")
def get_reviews(

    db: Session = Depends(
        get_db
    )

):

    reviews = (

        db.query(Review)

        .order_by(
            Review.id.desc()
        )

        .all()

    )


    result = []


    for review in reviews:

        result.append({

            "id":
            review.id,

            "repository":
            review.repository,

            "files_analyzed":
            review.files_analyzed,

            "security_score":
            review.security_score,

            "performance_score":
            review.performance_score,

            "code_quality_score":
            review.code_quality_score,

            "overall_score":
            review.overall_score,

            "issues":
            json.loads(
                review.issues
            ),

            "suggestions":
            json.loads(
                review.suggestions
            ),

            "created_at":
            review.created_at

        })


    return result


# ==========================================================
# GET SINGLE REVIEW
# ==========================================================

@app.get("/reviews/{review_id}")
def get_review(

    review_id: int,

    db: Session = Depends(
        get_db
    )

):

    review = (

        db.query(Review)

        .filter(
            Review.id == review_id
        )

        .first()

    )


    if review is None:

        raise HTTPException(

            status_code=404,

            detail="Review not found"

        )


    return {

        "id":
        review.id,

        "repository":
        review.repository,

        "files_analyzed":
        review.files_analyzed,

        "security_score":
        review.security_score,

        "performance_score":
        review.performance_score,

        "code_quality_score":
        review.code_quality_score,

        "overall_score":
        review.overall_score,

        "issues":
        json.loads(
            review.issues
        ),

        "suggestions":
        json.loads(
            review.suggestions
        ),

        "review":
        review.review_text,

        "created_at":
        review.created_at

    }


# ==========================================================
# DELETE REVIEW
# ==========================================================

@app.delete("/reviews/{review_id}")
def delete_review(

    review_id: int,

    db: Session = Depends(
        get_db
    )

):

    review = (

        db.query(Review)

        .filter(
            Review.id == review_id
        )

        .first()

    )


    if review is None:

        raise HTTPException(

            status_code=404,

            detail="Review not found"

        )


    db.delete(
        review
    )

    db.commit()


    return {

        "message":
        "Review deleted successfully"

    }


# ==========================================================
# DOCUMENTATION REQUEST
# ==========================================================

class DocumentationRequest(
    BaseModel
):

    repo_url: str

    report_type: str


# ==========================================================
# GENERATE DOCUMENTATION
# ==========================================================

@app.post("/generate-report")
def generate_report(

    data: DocumentationRequest

):

    try:

        allowed_types = {

            "srs",

            "snapshot",

            "evolution"

        }


        if data.report_type not in allowed_types:

            raise HTTPException(

                status_code=400,

                detail=(
                    "Invalid report type. "
                    "Use: srs, snapshot, evolution"
                )

            )


        repo_url = data.repo_url.strip()


        parts = (

            repo_url

            .rstrip("/")

            .split("/")

        )


        if len(parts) < 5:

            raise HTTPException(

                status_code=400,

                detail=
                "Invalid GitHub Repository URL"

            )


        owner = parts[-2]

        repo = parts[-1]


        try:

            branch = get_default_branch(

                owner,
                repo

            )


            code_files = get_code_files(

                owner,
                repo,
                branch

            )


        except GithubRateLimitError as e:

            raise HTTPException(

                status_code=429,

                detail=str(e)

            )


        except GithubNotFoundError as e:

            raise HTTPException(

                status_code=404,

                detail=str(e)

            )


        if not code_files:

            raise HTTPException(

                status_code=404,

                detail=
                "No supported source files found."

            )


        files = []


        for file_url in code_files[:8]:

            try:

                raw = requests.get(

                    file_url,

                    timeout=10

                )


                if raw.status_code != 200:

                    continue


                files.append({

                    "path":
                    file_url,

                    "content":
                    raw.text[:1800]

                })


            except Exception:

                continue


        if not files:

            raise HTTPException(

                status_code=404,

                detail=
                "No readable source files found."

            )


        repository = {

            "owner":
            owner,

            "repository":
            repo,

            "branch":
            branch,

            "language":
            "Unknown",

            "files":
            files

        }


        report = documentation_service.generate(

            report_type=
            data.report_type,

            repository=
            repository

        )


        return {

            "success": True,

            "repository":
            f"{owner}/{repo}",

            "branch":
            branch,

            "report_type":
            data.report_type,

            "report":
            report,

            "model":
            documentation_service.model

        }


    except HTTPException:

        raise


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )


# ==========================================================
# GENERATE DOCUMENTATION (PDF DOWNLOAD)
#
# Same inputs as /generate-report, but renders the markdown
# report into a PDF (via DocumentationService.create_pdf)
# and streams the file back for the browser to download.
# ==========================================================

REPORT_LABELS = {

    "srs": "SRS Report",

    "snapshot": "Project Snapshot",

    "evolution": "Evolution and Fix Plan"

}


@app.post("/generate-report-pdf")
def generate_report_pdf(

    data: DocumentationRequest

):

    try:

        allowed_types = {

            "srs",

            "snapshot",

            "evolution"

        }


        if data.report_type not in allowed_types:

            raise HTTPException(

                status_code=400,

                detail=(
                    "Invalid report type. "
                    "Use: srs, snapshot, evolution"
                )

            )


        repo_url = data.repo_url.strip()


        parts = (

            repo_url

            .rstrip("/")

            .split("/")

        )


        if len(parts) < 5:

            raise HTTPException(

                status_code=400,

                detail=
                "Invalid GitHub Repository URL"

            )


        owner = parts[-2]

        repo = parts[-1]


        try:

            branch = get_default_branch(

                owner,
                repo

            )


            code_files = get_code_files(

                owner,
                repo,
                branch

            )


        except GithubRateLimitError as e:

            raise HTTPException(

                status_code=429,

                detail=str(e)

            )


        except GithubNotFoundError as e:

            raise HTTPException(

                status_code=404,

                detail=str(e)

            )


        if not code_files:

            raise HTTPException(

                status_code=404,

                detail=
                "No supported source files found."

            )


        files = []


        for file_url in code_files[:8]:

            try:

                raw = requests.get(

                    file_url,

                    timeout=10

                )


                if raw.status_code != 200:

                    continue


                files.append({

                    "path":
                    file_url,

                    "content":
                    raw.text[:1800]

                })


            except Exception:

                continue


        if not files:

            raise HTTPException(

                status_code=404,

                detail=
                "No readable source files found."

            )


        repository = {

            "owner":
            owner,

            "repository":
            repo,

            "branch":
            branch,

            "language":
            "Unknown",

            "files":
            files

        }


        report_markdown = documentation_service.generate(

            report_type=
            data.report_type,

            repository=
            repository

        )


        label = REPORT_LABELS.get(

            data.report_type,

            "Report"

        )


        # ==================================================
        # Render to a temporary PDF file, then stream it
        # back. FileResponse handles reading the file; the
        # OS cleans up the temp directory eventually.
        # ==================================================

        temp_dir = tempfile.mkdtemp()

        pdf_filename = (
            f"{repo}-{data.report_type}.pdf"
        )

        pdf_path = os.path.join(
            temp_dir,
            pdf_filename
        )

        documentation_service.create_pdf(

            report=report_markdown,

            output_path=pdf_path,

            title=f"{label} - {owner}/{repo}"

        )


        return FileResponse(

            path=pdf_path,

            media_type="application/pdf",

            filename=pdf_filename

        )


    except HTTPException:

        raise


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )