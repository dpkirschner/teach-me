from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..config.sqlalchemy_db import get_db_session
from ..dao.job_dao import JobDAO
from ..services.job_service import JobService
from ..utils.logging import get_teach_me_logger, setup_teach_me_logger
from .models.job import JobRequest, JobResponse

# Configure logging
setup_teach_me_logger(level="INFO")
logger = get_teach_me_logger("api")

app = FastAPI()

# -- Exception Handlers --


@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError) -> JSONResponse:
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": str(exc)})


# -- Dependency Injection --


def get_job_service(session: Session = Depends(get_db_session)) -> JobService:
    """Dependency to get JobService instance."""
    return JobService(JobDAO(session), session)


# -- API Endpoints --


@app.post("/jobs/", status_code=201, response_model=JobResponse)
def create_job(job: JobRequest, service: JobService = Depends(get_job_service)) -> JobResponse:
    """Create a new job."""
    try:
        return service.create_job(job)
    except Exception as e:
        logger.error(f"Error creating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID, service: JobService = Depends(get_job_service)) -> JobResponse:
    """Get a job by ID."""
    job = service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found") from None
    return job


@app.get("/jobs/", response_model=list[JobResponse])
def get_jobs(
    limit: int = 100, offset: int = 0, service: JobService = Depends(get_job_service)
) -> list[JobResponse]:
    """Get all jobs with pagination."""
    return service.get_all_jobs(offset=offset, limit=limit)


@app.put("/jobs/{job_id}", response_model=JobResponse)
def update_job(job_id: UUID, job: JobRequest, service: JobService = Depends(get_job_service)) -> JobResponse:
    """Update a job by ID."""
    updated_job = service.update_job(job_id, job)
    if not updated_job:
        raise HTTPException(status_code=404, detail="Job not found") from None
    return updated_job


@app.delete("/jobs/{job_id}", status_code=200)
def delete_job(job_id: UUID, service: JobService = Depends(get_job_service)) -> dict:
    """Delete a job by ID."""
    if not service.delete_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found") from None
    return {"message": "Job deleted successfully"}
