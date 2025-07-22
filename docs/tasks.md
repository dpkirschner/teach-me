# Teach-Me: 3-Month AI Engineering Learning Plan

## Month 1 – Foundations & First LLM Micro-service

### Week 1 – Python Overhaul (15 hrs)

**Setup Tasks**
```bash
# 1. Create new project structure
mkdir teach-me && cd teach-me
git init
python3.11 -m venv venv  # ⚠️ Python 3.11+ required for latest features
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install fastapi httpx pydantic python-dotenv
pip install pytest pytest-cov pytest-asyncio ruff mypy types-requests

# 3. Create project structure
mkdir -p src/teach_me tests docs .github/workflows
touch src/teach_me/__init__.py
```

**Configuration Files to Create**
1. `pyproject.toml` - Configure ruff, mypy, pytest with modern Python standards
2. `.env.example` - Template for API keys (OpenAI, Anthropic)
3. `Makefile` - Commands for lint, test, type-check

**Refactoring Tasks**
1. Choose an existing Python project or create a weather fetcher service
2. Add type hints to all functions (use `typing.Optional`, `typing.Dict`, etc.)
3. Convert blocking I/O to async/await patterns
4. Add Pydantic models for request/response validation
5. Implement proper error handling with custom exceptions

**CI/CD Setup**
```bash
# Create .github/workflows/ci.yml
# Configure GitHub Actions to:
# - Run on Python 3.11
# - Install dependencies with pip
# - Run: make lint (ruff check)
# - Run: make type (mypy)
# - Run: make test (pytest with coverage)
# - Fail if coverage < 80%
```

**Deliverable Checklist**
- [ ] All functions have type hints
- [ ] 100% mypy compliance in strict mode
- [ ] Ruff passes with no errors
- [ ] Test coverage > 80%
- [ ] CI badge green on GitHub

---

### Week 2 – AWS Setup (15 hrs)

**⚠️ Cost Warning**: AWS charges will apply. Set up billing alerts at $50/month.

**Initial AWS Setup**
```bash
# 1. Install AWS tools
pip install awscli aws-cdk-lib constructs boto3

# 2. Configure AWS credentials (create IAM user with limited permissions)
aws configure
# Use us-east-1 for best service availability

# 3. Bootstrap CDK
cdk bootstrap aws://ACCOUNT-ID/us-east-1
```

**IAM Configuration Tasks**
1. Create IAM user `teach-me-dev` with programmatic access
2. Create custom policy with minimal permissions:
   - Lambda: Create/Update/Delete functions
   - API Gateway: Manage APIs
   - CloudWatch: Write logs, create dashboards
   - ECR: Push/pull images
   - IAM: Manage Lambda execution roles only

**CDK Project Structure**
```bash
mkdir infrastructure && cd infrastructure
cdk init app --language=python
```

**CDK Stack Components**
```json
{
  "lambda_config": {
    "runtime": "python3.11",
    "memory_size": 512,
    "timeout": 30,
    "environment": {
      "LOG_LEVEL": "INFO"
    }
  },
  "api_gateway_config": {
    "stage": "dev",
    "throttle": {
      "rate_limit": 10,
      "burst_limit": 20
    }
  }
}
```

**Tasks to Complete**
1. Create Lambda function with FastAPI handler
2. Configure API Gateway with Lambda proxy integration
3. Set up CloudWatch log groups with 7-day retention
4. Create deployment script that outputs API endpoint URL
5. Test with curl: `curl https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/dev/`

---

### Week 3 – Hugging Face Crash Course (15 hrs)

**Local Setup Tasks**
```bash
# Install ML dependencies
pip install transformers torch torchvision accelerate datasets
pip install docker  # For containerization
```

**Model Selection**
- Use `distilbert-base-uncased` for sentiment analysis (65MB, good for CPU)
- ⚠️ GPU costs: Avoid for now unless you have local GPU

**Benchmarking Tasks**
1. Download model and tokenizer locally
2. Create benchmark script measuring:
   - Tokens per second
   - Memory usage
   - P95 latency for batch sizes [1, 8, 16, 32]
3. Compare CPU vs MPS (if on Mac M1/M2)

**Docker Container Tasks**
```bash
# Build minimal inference container
# Base image: python:3.11-slim
# Size target: < 1GB
# Include only: transformers, torch (CPU), model files
```

**AWS Deployment**
1. Create ECR repository: `teach-me-models`
2. Push container with tags: `distilbert-sentiment:v1`
3. Create Lambda function from container image
4. ⚠️ Cold start will be 10-15 seconds due to model loading

**CloudWatch Dashboard Metrics**
```json
{
  "metrics_to_track": [
    "Lambda Duration",
    "Lambda Concurrent Executions", 
    "Lambda Throttles",
    "Custom: tokens_per_second",
    "Custom: model_load_time"
  ]
}
```

---

### Week 4 – LLM API Wrapper Micro-service (15 hrs)

**API Keys Setup**
```bash
# Add to .env file
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
# ⚠️ Cost Warning: Set usage limits in both platforms
```

**FastAPI Service Structure**
```json
{
  "endpoints": {
    "/health": "Basic health check",
    "/prompt": {
      "method": "POST",
      "request_body": {
        "prompt": "string",
        "model": "gpt-4o | claude-3-sonnet",
        "max_tokens": 1000,
        "stream": false
      },
      "response": {
        "text": "string",
        "model_used": "string",
        "tokens_used": 123,
        "latency_ms": 456
      }
    },
    "/prompt/stream": "SSE endpoint for streaming"
  }
}
```

**Implementation Tasks**
1. Create unified interface for both OpenAI and Anthropic APIs
2. Implement retry logic with exponential backoff
3. Add request/response logging with correlation IDs
4. Create cost tracking middleware
5. Implement rate limiting per API key

**Lambda Deployment Configuration**
```json
{
  "provisioned_concurrency": 1,
  "reserved_concurrent_executions": 10,
  "environment_variables": {
    "API_KEYS_SECRET_NAME": "teach-me/api-keys"
  }
}
```

**Testing Tasks**
1. Create integration tests using `pytest-httpx` for mocking
2. Load test with 10 concurrent requests
3. Measure cold start vs warm start latency
4. Document cost per 1K tokens for each model

**Deliverable Demo**
```bash
# Create README with gif showing:
curl -X POST https://your-api.execute-api.us-east-1.amazonaws.com/dev/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum computing in one sentence", "model": "gpt-4o"}'
```

---

## Month 2 – Retrieval-Augmented Chatbot (RAG)

### Week 5 – Vector DB Evaluation (15 hrs)

**Database Setup Tasks**
```bash
# Option 1: pgvector on RDS (⚠️ ~$50/month for smallest instance)
# Option 2: Chroma on ECS Fargate (⚠️ ~$30/month)
# Option 3: Local development with Docker (free)
```

**Test Dataset Preparation**
1. Download ArXiv abstracts dataset (5000 documents)
2. Create 50 test queries with relevance labels
3. Split into chunks of 512 tokens with 50 token overlap

**Evaluation Metrics Script**
```json
{
  "metrics": {
    "recall_at_k": [1, 5, 10],
    "mean_reciprocal_rank": true,
    "latency_percentiles": ["p50", "p95", "p99"]
  },
  "embedding_models": [
    "text-embedding-ada-002",
    "BAAI/bge-base-en-v1.5"
  ]
}
```

**Comparison Tasks**
1. Load same dataset into both pgvector and Chroma
2. Run evaluation queries 3x and average results
3. Measure: index build time, query latency, accuracy
4. Create Jupyter notebook with visualization
5. Export results to `results/vector_db_comparison.csv`

---

### Week 6 – Doc Ingestion Pipeline (15 hrs)

**Pipeline Architecture**
```json
{
  "steps": [
    {"name": "fetch", "type": "Lambda"},
    {"name": "extract_text", "type": "Lambda"},
    {"name": "chunk", "type": "Lambda"},
    {"name": "embed", "type": "Lambda", "config": {"batch_size": 100}},
    {"name": "store", "type": "Lambda"}
  ],
  "orchestration": "Step Functions Express"
}
```

**Document Sources**
1. Web scraper for documentation sites
2. PDF processor using PyPDF2
3. Markdown/RST file reader
4. GitHub repo documentation crawler

**Chunking Strategy Tasks**
1. Implement semantic chunking (split on paragraphs/sections)
2. Add metadata: source, timestamp, section headers
3. Handle code blocks specially (don't split)
4. Create overlap for context continuity

**Step Functions Tasks**
```bash
# Create state machine with:
# - Parallel processing for multiple documents
# - Error handling with DLQ
# - CloudWatch metrics for each step
# - Cost optimization: use Express workflows
```

---

### Week 7 – RAG API (15 hrs)

**API Design**
```json
{
  "endpoints": {
    "/chat": {
      "method": "POST",
      "request": {
        "message": "string",
        "context_window": 5,
        "temperature": 0.7
      },
      "response": {
        "answer": "string",
        "sources": [
          {"text": "...", "score": 0.89, "metadata": {}}
        ],
        "search_quality": "high|medium|low"
      }
    }
  }
}
```

**RAG Pipeline Tasks**
1. Query rewriting for better retrieval
2. Hybrid search: combine vector + keyword search
3. Re-ranking with cross-encoder
4. Prompt template management
5. Answer quality scoring

**Fallback Strategy**
```json
{
  "conditions": {
    "no_results": "Return general response",
    "low_confidence": "Add disclaimer",
    "conflicting_sources": "Present multiple viewpoints"
  }
}
```

**Testing Suite**
1. Create 20 golden Q&A pairs
2. Test edge cases: out-of-domain, adversarial
3. Measure: answer accuracy, source attribution
4. Add hallucination detection tests

---

### Week 8 – Frontend Demo (15 hrs)

**Next.js Setup Tasks**
```bash
npx create-next-app@latest teach-me-chat --typescript --tailwind --app
cd teach-me-chat
npm install @aws-sdk/client-lambda ai uuid
```

**Frontend Components**
```json
{
  "components": {
    "ChatInterface": "Message bubbles with typing indicator",
    "SourceCards": "Expandable citations with relevance scores",
    "StreamingResponse": "Token-by-token display with SSE",
    "CostMeter": "Real-time cost tracking display"
  }
}
```

**AWS Integration Tasks**
1. Create Cognito user pool for auth (optional)
2. Use API Gateway API key for simple auth
3. Implement request signing with AWS SDK
4. Add CORS configuration

**Deployment Tasks**
1. Deploy to Vercel (free tier)
2. Set environment variables for API endpoint
3. Configure custom domain (optional)
4. Add analytics with Vercel Analytics

**Demo Video Script**
1. Show chat interface
2. Ask technical question
3. Highlight streaming response
4. Click on sources to show context
5. Show cost tracking

---

## Month 3 – Agents, GPU Inference, and MLOps Hardening

### Week 9 – LangChain Agent with Tool Calls (15 hrs)

**Agent Architecture**
```json
{
  "tools": [
    {"name": "web_search", "api": "SerpAPI", "cost_per_call": 0.001},
    {"name": "calculator", "type": "built-in"},
    {"name": "rag_search", "type": "custom", "endpoint": "/chat"}
  ],
  "agent_config": {
    "type": "ReAct",
    "max_iterations": 5,
    "early_stopping": true
  }
}
```

**Security Testing Tasks**
1. Create prompt injection test cases:
   - "Ignore previous instructions and..."
   - Hidden instructions in tool outputs
   - Recursive tool calling attempts
2. Implement safeguards:
   - Tool call limits
   - Output validation
   - Sensitive data filtering

**Tool Implementation**
1. Web search with result summarization
2. Calculator with symbolic math support
3. RAG integration with confidence scores
4. Error handling for tool failures

**Test Suite with Pytest**
```bash
# Create parametrized tests for:
# - Normal queries (20 cases)
# - Edge cases (10 cases)  
# - Security tests (15 cases)
# - Performance tests (concurrent requests)
```

---

### Week 10 – Cost/Latency Observability (15 hrs)

**Structured Logging Format**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "uuid",
  "user_id": "anonymous",
  "operation": "chat_completion",
  "model": "gpt-4o",
  "tokens": {"prompt": 150, "completion": 200},
  "cost_usd": 0.0105,
  "latency_ms": 1250,
  "status": "success"
}
```

**CloudWatch to Grafana Pipeline**
1. Configure CloudWatch Logs Insights queries
2. Set up Amazon Managed Grafana workspace
3. Create IAM role for Grafana data source
4. Build dashboards for:
   - Request volume by endpoint
   - Cost breakdown by model
   - P50/P95/P99 latencies
   - Error rates and types

**Alerts Configuration**
```json
{
  "alerts": [
    {"metric": "cost_per_hour", "threshold": 10, "action": "email"},
    {"metric": "error_rate", "threshold": 0.05, "action": "slack"},
    {"metric": "p99_latency", "threshold": 5000, "action": "page"}
  ]
}
```

---

### Week 11 – GPU Inference Benchmark (15 hrs)

**⚠️ Cost Warning**: g5.xlarge costs ~$1/hour. Set 4-hour auto-terminate.

**EC2 Setup Script**
```bash
# Launch with Ubuntu Deep Learning AMI
# Install: vLLM, TGI, or llama.cpp
# Download: Llama-3-8B quantized models (Q4, Q8)
```

**Benchmark Test Matrix**
```json
{
  "models": ["Llama-3-8B-Q4", "Llama-3-8B-Q8"],
  "batch_sizes": [1, 4, 8, 16],
  "metrics": {
    "throughput": "tokens/second",
    "latency": "time to first token",
    "memory": "GPU memory usage",
    "cost": "$/1M tokens"
  }
}
```

**Comparison Tasks**
1. Run same prompts through:
   - GPU inference server
   - OpenAI API (GPT-4o)
   - Anthropic API (Claude)
2. Create cost-performance curves
3. Identify break-even point for self-hosting

**Report Structure**
- Executive summary with recommendations
- Detailed benchmark results in CSV
- Visualization of cost vs performance
- TCO analysis including infrastructure

---

### Week 12 – CI/CD & Rollback (15 hrs)

**⚠️ Kubernetes costs**: EKS costs ~$75/month. Consider using Kind for local testing.

**Kubernetes Setup**
```bash
# Option 1: EKS with eksctl
# Option 2: Local Kind cluster for testing
# Create: namespace, deployments, services, ingress
```

**Helm Chart Structure**
```json
{
  "services": {
    "rag-api": {
      "replicas": 2,
      "resources": {"memory": "512Mi", "cpu": "500m"}
    },
    "agent-api": {
      "replicas": 2,
      "resources": {"memory": "1Gi", "cpu": "1000m"}
    }
  }
}
```

**Blue-Green Deployment Tasks**
1. Create two environments: blue (stable), green (new)
2. Implement health checks for readiness
3. Create switching mechanism via ingress
4. Add smoke tests before switch

**Evaluation Harness**
```json
{
  "tests": [
    {"type": "functional", "weight": 0.7},
    {"type": "performance", "weight": 0.2},
    {"type": "cost", "weight": 0.1}
  ],
  "rollback_threshold": 0.95
}
```

**GitHub Actions Workflow**
1. Trigger on push to main
2. Build and push Docker images
3. Deploy to green environment
4. Run evaluation harness
5. Auto-rollback if score drops >5%
6. Switch traffic if tests pass
7. Clean up old blue environment

**Demo Recording Tasks**
1. Make intentional breaking change
2. Show automated deployment
3. Display evaluation scores dropping
4. Capture automatic rollback
5. Show system recovering to stable state