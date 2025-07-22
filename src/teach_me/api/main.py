from datetime import datetime
from uuid import UUID, uuid4
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class JobRequest(BaseModel):
    content: str


class JobResponse(BaseModel):
    id: UUID
    created_at: datetime


@app.post("/jobs/", status_code=201)
async def create_job(job: JobRequest) -> JobResponse:
    return JobResponse(
        id=uuid4(),
        created_at=datetime.now()
    )
