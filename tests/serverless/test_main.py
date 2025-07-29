import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.serverless.main import app


@pytest.fixture
def mock_classifier():
    classifier = MagicMock()
    classifier.return_value = [
        [{"label": "POSITIVE", "score": 0.9998}, {"label": "NEGATIVE", "score": 0.0002}]
    ]
    return classifier


@pytest.fixture
def client_with_mocked_model(mock_classifier):
    with patch("src.serverless.main.pipeline") as mock_pipeline:
        mock_pipeline.return_value = mock_classifier

        with TestClient(app) as client:
            yield client


class TestHealthCheck:
    def test_root_endpoint(self, client_with_mocked_model):
        response = client_with_mocked_model.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "message": "Sentiment Analysis API is running"}


class TestModelLoading:
    @patch.dict(os.environ, {"MODEL_NAME": "custom-model", "MODEL_PATH": "/custom/path"})
    @patch("src.serverless.main.os.path.isdir")
    @patch("src.serverless.main.pipeline")
    def test_model_loading_with_custom_path_exists(self, mock_pipeline, mock_isdir):
        mock_isdir.return_value = True
        mock_pipeline.return_value = MagicMock()

        with TestClient(app):
            pass

        mock_pipeline.assert_called_once_with(
            task="text-classification", model="/custom/path", return_all_scores=True
        )

    @patch.dict(os.environ, {"MODEL_NAME": "custom-model", "MODEL_PATH": "/custom/path"})
    @patch("src.serverless.main.os.path.isdir")
    @patch("src.serverless.main.pipeline")
    def test_model_loading_with_custom_path_not_exists(self, mock_pipeline, mock_isdir):
        mock_isdir.return_value = False
        mock_pipeline.return_value = MagicMock()

        with TestClient(app):
            pass

        mock_pipeline.assert_called_once_with(
            task="text-classification", model="custom-model", return_all_scores=True
        )

    @patch("src.serverless.main.pipeline")
    def test_model_loading_default_model(self, mock_pipeline):
        mock_pipeline.return_value = MagicMock()

        with TestClient(app):
            pass

        mock_pipeline.assert_called_once_with(
            task="text-classification",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            return_all_scores=True,
        )


class TestSentimentPrediction:
    def test_successful_prediction_single_instance(self, client_with_mocked_model):
        request_data = {"instances": [{"text": "I love this product!"}]}

        response = client_with_mocked_model.post("/invocations", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert len(data["predictions"]) == 1

        prediction = data["predictions"][0]
        assert "top_prediction" in prediction
        assert "all_scores" in prediction
        assert prediction["top_prediction"]["label"] == "POSITIVE"
        assert prediction["top_prediction"]["score"] == 0.9998

    def test_successful_prediction_multiple_instances(self, client_with_mocked_model):
        app.state.classifier.return_value = [
            [{"label": "POSITIVE", "score": 0.9998}, {"label": "NEGATIVE", "score": 0.0002}],
            [{"label": "NEGATIVE", "score": 0.8888}, {"label": "POSITIVE", "score": 0.1112}],
        ]

        request_data = {"instances": [{"text": "I love this product!"}, {"text": "This is terrible"}]}

        response = client_with_mocked_model.post("/invocations", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 2

        assert data["predictions"][0]["top_prediction"]["label"] == "POSITIVE"
        assert data["predictions"][1]["top_prediction"]["label"] == "NEGATIVE"

    def test_prediction_with_empty_text(self, client_with_mocked_model):
        request_data = {"instances": [{"text": ""}]}

        response = client_with_mocked_model.post("/invocations", json=request_data)

        assert response.status_code == 422

    def test_prediction_with_all_empty_texts(self, client_with_mocked_model):
        request_data = {"instances": [{"text": ""}, {"text": ""}]}

        response = client_with_mocked_model.post("/invocations", json=request_data)

        assert response.status_code == 422

    def test_prediction_with_mixed_empty_and_valid_texts(self, client_with_mocked_model):
        request_data = {"instances": [{"text": ""}, {"text": "This is great!"}]}

        response = client_with_mocked_model.post("/invocations", json=request_data)

        assert response.status_code == 422


class TestErrorHandling:
    def test_invalid_request_format(self, client_with_mocked_model):
        request_data = {"invalid_field": "invalid_value"}

        response = client_with_mocked_model.post("/invocations", json=request_data)
        assert response.status_code == 422

    def test_missing_text_field(self, client_with_mocked_model):
        request_data = {"instances": [{"not_text": "I love this product!"}]}

        response = client_with_mocked_model.post("/invocations", json=request_data)
        assert response.status_code == 422

    def test_classifier_exception(self, client_with_mocked_model):
        app.state.classifier.side_effect = Exception("Model inference failed")

        request_data = {"instances": [{"text": "I love this product!"}]}

        response = client_with_mocked_model.post("/invocations", json=request_data)

        assert response.status_code == 500
        assert "internal error" in response.json()["detail"]

    def test_empty_instances_list(self, client_with_mocked_model):
        request_data = {"instances": []}

        response = client_with_mocked_model.post("/invocations", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert isinstance(data["predictions"], list)
        assert len(data["predictions"]) == 0


class TestResponseFormat:
    def test_response_schema_compliance(self, client_with_mocked_model):
        app.state.classifier.return_value = [
            [{"label": "POSITIVE", "score": 0.9998}, {"label": "NEGATIVE", "score": 0.0002}]
        ]

        request_data = {"instances": [{"text": "I love this product!"}]}

        response = client_with_mocked_model.post("/invocations", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Check top-level structure
        assert "predictions" in data
        assert isinstance(data["predictions"], list)

        # Check prediction structure
        prediction = data["predictions"][0]
        assert "top_prediction" in prediction
        assert "all_scores" in prediction

        # Check top_prediction structure
        top_pred = prediction["top_prediction"]
        assert "label" in top_pred
        assert "score" in top_pred
        assert isinstance(top_pred["label"], str)
        assert isinstance(top_pred["score"], float)

        # Check all_scores structure
        all_scores = prediction["all_scores"]
        assert isinstance(all_scores, list)
        assert len(all_scores) == 2

        for score in all_scores:
            assert "label" in score
            assert "score" in score
            assert isinstance(score["label"], str)
            assert isinstance(score["score"], float)
