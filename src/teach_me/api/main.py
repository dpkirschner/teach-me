from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from ..config.sqlalchemy_db import get_db_session
from ..dao.job_dao import JobDAO
from ..schemas.job import JobRequest, JobResponse
from ..services.job_service import JobService
from ..utils.logging import get_teach_me_logger, setup_teach_me_logger

# Configure teach_me namespace logging
setup_teach_me_logger(level="INFO")
logger = get_teach_me_logger("api")

app = FastAPI()


# Create dependency variables to avoid B008 warning
_db_session_dependency = Depends(get_db_session)


def get_job_dao(session: Session = _db_session_dependency) -> JobDAO:
    """Dependency to get JobDAO instance."""
    logger.debug("Creating JobDAO with session")
    return JobDAO(session)


def get_job_service(session: Session = _db_session_dependency) -> JobService:
    """Dependency to get JobService instance."""
    logger.debug("Creating JobService with session and DAO")
    job_dao = JobDAO(session)
    return JobService(job_dao, session)


# Define dependencies after the functions are created
_job_dao_dependency = Depends(get_job_dao)
_job_service_dependency = Depends(get_job_service)


@app.post("/jobs/", status_code=201, response_model=JobResponse)
def create_job(job: JobRequest, job_service: JobService = _job_service_dependency) -> JobResponse:
    """Create a new job."""
    logger.debug(f"Creating job with content: {job.content}")
    try:
        return job_service.create_job(job)
    except ValueError as e:
        logger.warning(f"Validation error creating job: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error creating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID, job_service: JobService = _job_service_dependency) -> JobResponse:
    """Get a job by ID."""
    try:
        job = job_service.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/jobs/", response_model=list[JobResponse])
def get_jobs(
    limit: int = 100, offset: int = 0, job_service: JobService = _job_service_dependency
) -> list[JobResponse]:
    """Get all jobs with pagination."""
    logger.debug(f"Getting jobs with limit: {limit}, offset: {offset}")
    try:
        jobs = job_service.get_all_jobs(offset=offset, limit=limit)
        logger.debug(f"Retrieved {len(jobs)} jobs")
        return jobs
    except Exception as e:
        logger.error(f"Error getting jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.put("/jobs/{job_id}", response_model=JobResponse)
def update_job(
    job_id: UUID, job: JobRequest, job_service: JobService = _job_service_dependency
) -> JobResponse:
    """Update a job by ID."""
    try:
        updated_job = job_service.update_job(job_id, job)
        if not updated_job:
            raise HTTPException(status_code=404, detail="Job not found")
        return updated_job
    except ValueError as e:
        logger.warning(f"Validation error updating job {job_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/jobs/{job_id}")
def delete_job(job_id: UUID, job_service: JobService = _job_service_dependency) -> dict:
    """Delete a job by ID."""
    try:
        deleted = job_service.delete_job(job_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"message": "Job deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
