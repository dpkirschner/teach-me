from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException

from ..config.database import get_supabase_client
from ..dao.job_dao import JobDAO
from ..models.job import JobCreate, JobUpdate
from ..schemas.job import JobRequest, JobResponse
from ..utils.logging import get_teach_me_logger, setup_teach_me_logger

# Configure teach_me namespace logging
setup_teach_me_logger(level="DEBUG")
logger = get_teach_me_logger("api")

app = FastAPI()


def get_job_dao() -> JobDAO:
    """Dependency to get JobDAO instance."""
    logger.debug("Getting Supabase client")
    try:
        supabase = get_supabase_client()
        logger.debug(f"Supabase client created successfully: {supabase}")
        dao = JobDAO(supabase)
        logger.debug("JobDAO created successfully")
        return dao
    except Exception as e:
        logger.error(f"Error creating JobDAO: {e}")
        raise


@app.post("/jobs/", status_code=201, response_model=JobResponse)
def create_job(job: JobRequest, job_dao: JobDAO = Depends(get_job_dao)) -> JobResponse:  # noqa: B008
    """Create a new job."""
    logger.debug(f"Creating job with content: {job.content}")
    try:
        job_data = JobCreate(content=job.content)
        logger.debug(f"JobCreate model: {job_data}")

        logger.debug("Calling job_dao.create")
        created_job = job_dao.create(job_data)
        logger.debug(f"Created job: {created_job}")

        response = JobResponse(
            id=created_job.id,
            content=created_job.content,
            created_at=created_job.created_at,
        )
        logger.debug(f"Returning response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error creating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID, job_dao: JobDAO = Depends(get_job_dao)) -> JobResponse:  # noqa: B008
    """Get a job by ID."""
    try:
        job = job_dao.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobResponse(id=job.id, content=job.content, created_at=job.created_at)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/jobs/", response_model=list[JobResponse])
def get_jobs(limit: int = 100, offset: int = 0, job_dao: JobDAO = Depends(get_job_dao)) -> list[JobResponse]:  # noqa: B008
    """Get all jobs with pagination."""
    try:
        jobs = job_dao.get_all(limit=limit, offset=offset)
        return [JobResponse(id=job.id, content=job.content, created_at=job.created_at) for job in jobs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.put("/jobs/{job_id}", response_model=JobResponse)
def update_job(job_id: UUID, job: JobRequest, job_dao: JobDAO = Depends(get_job_dao)) -> JobResponse:  # noqa: B008
    """Update a job by ID."""
    try:
        job_data = JobUpdate(content=job.content)
        updated_job = job_dao.update(job_id, job_data)
        if not updated_job:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobResponse(
            id=updated_job.id,
            content=updated_job.content,
            created_at=updated_job.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/jobs/{job_id}")
def delete_job(job_id: UUID, job_dao: JobDAO = Depends(get_job_dao)) -> dict:  # noqa: B008
    """Delete a job by ID."""
    try:
        deleted = job_dao.delete(job_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Job not found")

        return {"message": "Job deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
