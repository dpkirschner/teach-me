import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from mangum import Mangum
from pydantic import BaseModel, Field
from transformers import pipeline

# Setup a logger for better debugging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Instance(BaseModel):
    text: str = Field(..., min_length=1)


class Score(BaseModel):
    label: str
    score: float


class Prediction(BaseModel):
    top_prediction: Score
    all_scores: list[Score]


class SentimentRequest(BaseModel):
    instances: list[Instance] = Field(..., max_items=100)


class SentimentResponse(BaseModel):
    predictions: list[Prediction]


# --- Lifespan and Model Loading ---

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    MODEL_NAME = os.getenv("MODEL_NAME", "distilbert-base-uncased-finetuned-sst-2-english")
    MODEL_PATH = os.getenv("MODEL_PATH", f"./{MODEL_NAME}") # Default to a local path

    model_source = MODEL_PATH if os.path.isdir(MODEL_PATH) else MODEL_NAME
    logger.info(f"Loading model from: {model_source}")

    # The pipeline handles model and tokenizer loading automatically
    app.state.classifier = pipeline(
        task="text-classification", model=model_source, return_all_scores=True
    )
    logger.info("Model loaded successfully.")
    
    yield
    
    app.state.classifier = None


# --- FastAPI App ---

app = FastAPI(
    lifespan=lifespan,
    title="Sentiment Analysis API",
    description="API for sentiment analysis using a distilled BERT model.",
)


@app.get("/", tags=["Health Check"])
async def read_root() -> dict[str, str]:
    return {"status": "ok", "message": "Sentiment Analysis API is running"}


@app.post("/invocations", response_model=SentimentResponse, tags=["Prediction"])
async def predict_sentiment(request: SentimentRequest) -> SentimentResponse:
    try:
        texts = [instance.text for instance in request.instances]
        results: list[list[dict[str, Any]]] = app.state.classifier(texts)

        predictions = [
            Prediction(
                top_prediction=Score(**score_list[0]),
                all_scores=[Score(**s) for s in score_list],
            )
            for score_list in results
        ]

        return SentimentResponse(predictions=predictions)

    except Exception as e:
        # Log the full exception for debugging
        logger.error(f"Prediction failed: {e}", exc_info=True)
        # Return a generic error message to the client
        raise HTTPException(status_code=500, detail="An internal error occurred during prediction.")


handler = Mangum(app)