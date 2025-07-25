from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()


@app.get("/")
def read_root() -> dict:
    return {"message": "Hello from FastAPI on AWS Lambda!"}


handler = Mangum(app)
