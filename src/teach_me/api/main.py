from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from ..config.sqlalchemy_db import get_db_session
from ..dao.job_dao import JobDAO
from ..models.request.job import JobCreate, JobUpdate
from ..schemas.job import JobRequest, JobResponse
from ..utils.logging import get_teach_me_logger, setup_teach_me_logger

# Configure teach_me namespace logging
setup_teach_me_logger(level="INFO")
logger = get_teach_me_logger("api")

app = FastAPI()


# Create dependency variables to avoid B008 warning
_db_session_dependency = Depends(get_db_session)


def get_job_dao(session: Session = _db_session_dependency) -> JobDAO:
    """Dependency to get JobSQLAlchemyDAO instance."""
    logger.debug("Creating JobSQLAlchemyDAO with session")
    return JobDAO(session)


# Define this after the function is created
_job_dao_dependency = Depends(get_job_dao)


@app.post("/jobs/", status_code=201, response_model=JobResponse)
def create_job(job: JobRequest, job_dao: JobDAO = _job_dao_dependency) -> JobResponse:
    """Create a new job."""
    logger.debug(f"Creating job with content: {job.content}")
    try:
        job_data = JobCreate(content=job.content)
        created_job = job_dao.create(job_data)

        # Commit the transaction
        job_dao.session.commit()

        response = JobResponse(
            id=created_job.id,
            content=created_job.content,
            created_at=created_job.created_at,
        )
        logger.debug(f"Returning response: {response}")
        return response
    except Exception as e:
        job_dao.session.rollback()
        logger.error(f"Error creating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID, job_dao: JobDAO = _job_dao_dependency) -> JobResponse:
    """Get a job by ID."""
    try:
        job = job_dao.get_by_id(job_id)
        job_dao.session.commit()  # Ensure we're reading committed data
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobResponse(id=job.id, content=job.content, created_at=job.created_at)
    except HTTPException:
        raise
    except Exception as e:
        job_dao.session.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/jobs/", response_model=list[JobResponse])
def get_jobs(limit: int = 100, offset: int = 0, job_dao: JobDAO = _job_dao_dependency) -> list[JobResponse]:
    """Get all jobs with pagination."""
    logger.debug(f"Getting jobs with limit: {limit}, offset: {offset}")
    try:
        jobs = job_dao.get_all(limit=limit, offset=offset)
        job_dao.session.commit()
        logger.debug(f"Retrieved {len(jobs)} jobs")
        return [JobResponse(id=job.id, content=job.content, created_at=job.created_at) for job in jobs]
    except Exception as e:
        job_dao.session.rollback()
        logger.error(f"Error getting jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.put("/jobs/{job_id}", response_model=JobResponse)
def update_job(job_id: UUID, job: JobRequest, job_dao: JobDAO = _job_dao_dependency) -> JobResponse:
    """Update a job by ID."""
    try:
        job_data = JobUpdate(content=job.content)
        updated_job = job_dao.update(job_id, job_data)
        if not updated_job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Commit the transaction
        job_dao.session.commit()

        return JobResponse(
            id=updated_job.id,
            content=updated_job.content,
            created_at=updated_job.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        job_dao.session.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/jobs/{job_id}")
def delete_job(job_id: UUID, job_dao: JobDAO = _job_dao_dependency) -> dict:
    """Delete a job by ID."""
    try:
        deleted = job_dao.delete(job_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Job not found")

        # Commit the transaction
        job_dao.session.commit()

        return {"message": "Job deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        job_dao.session.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
