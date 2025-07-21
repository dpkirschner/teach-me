# 12-Week AI-Engineer Transition Plan (15 hrs/week, AWS-centric)

## Rhythm
- **3 sessions × 5 hrs** each week (e.g., Tue/Thu/Sat).  
- Every Saturday ends with a *commit, demo video, and journal entry* pushed to GitHub.

---

## Month 1  –  Foundations & First LLM Micro-service

### Week 1  (15 hrs)
- **Python overhaul**  
  - Add `ruff`, `mypy`, `pytest-cov` to a new repo.  
  - Refactor one of your old side projects to use async + type hints.  
- **Deliverable**: GitHub repo with CI (GitHub Actions) running tests and lint on push.

### Week 2  (15 hrs)
- **AWS setup**  
  - Configure IAM least-privilege roles, ECR, CloudWatch log groups.  
  - Create an AWS CDK skeleton (Python) that can deploy Lambda + API Gateway.  
- **Deliverable**: CDK repo deploying “Hello World” FastAPI in Lambda.

### Week 3  (15 hrs)
- **Hugging Face crash course**  
  - Local inference benchmark on `distilbert-base-uncased` (CPU vs M1/GPU if available).  
  - Package model + handler into a Docker image → push to ECR.  
- **Deliverable**: CloudWatch dashboard showing p95 latency & tokens/sec.

### Week 4  (15 hrs)
- **LLM API wrapper micro-service**  
  - FastAPI route `/prompt` calling OpenAI GPT-4o and Anthropic Claude.  
  - Response schema + streaming.  
  - Deploy via Lambda URL with provisioned concurrency=1.  
- **Deliverable**: Public endpoint + README gif of curl request.

---

## Month 2  –  Retrieval-Augmented Chatbot (RAG)

### Week 5  (15 hrs)
- **Vector DB evaluation**  
  - Spin up **pgvector** on Amazon RDS + **Chroma** in ECS Fargate.  
  - Load 5 k markdown docs; measure recall@5 on 50 labelled queries.  
- **Deliverable**: Jupyter notebook + metrics CSV committed.

### Week 6  (15 hrs)
- **Doc ingestion pipeline**  
  - Scraper → text cleaner → chunker → embeddings (OpenAI Ada 002 vs BGE-base).  
  - Orchestrate with AWS Step Functions Express.  
- **Deliverable**: State Machine diagram + step timings.

### Week 7  (15 hrs)
- **RAG API**  
  - FastAPI route `/chat` → similarity search → prompt compose → GPT-4o.  
  - Guard against empty hits with fallback heuristic.  
- **Deliverable**: End-to-end unit tests (pytest) w/ golden answers.

### Week 8  (15 hrs)
- **Frontend demo**  
  - Next.js 14 app (TypeScript) with streaming SSE tokens and source citations.  
  - Deploy on Vercel; connect to AWS API Gateway via signed requests.  
- **Deliverable**: Short Loom video demo; link added to résumé.

---

## Month 3  –  Agents, GPU Inference, and MLOps Hardening

### Week 9  (15 hrs)
- **LangChain Agent w/ tool calls**  
  - Tools: web search (SerpAPI), calculator, internal RAG.  
  - Add prompt-injection test cases (pytest parametrize).  
- **Deliverable**: Pass/fail security test report in CI.

### Week 10  (15 hrs)
- **Cost / latency observability**  
  - Emit structured logs to CloudWatch → pipe to Amazon Managed Grafana.  
  - Dashboards: tokens/request, $/request, p95 latency, 4xx/5xx.  
- **Deliverable**: Screenshot of live dashboard linked in README.

### Week 11  (15 hrs)
- **GPU inference benchmark**  
  - Spin up `g5.xlarge` EC2 w/ NVIDIA A10G; run quantized `Llama-3-8B-Q4`.  
  - Compare throughput vs Lambda GPT-4o proxy; log cost curves.  
- **Deliverable**: Markdown report + CSV cost-latency table.

### Week 12  (15 hrs)
- **CI/CD & rollback**  
  - GitHub Actions → EKS Blue/Green deploy of RAG + agent services (Helm).  
  - Canary test hitting eval harness; auto-rollback if score↓ >5 %.  
- **Deliverable**: Cast-away video of a failed deploy triggering rollback.

---

## Stretch (post-Week 12 if time remains)
- Automate retraining on new docs (SageMaker Pipelines).  
- Experiment tracking w/ Weights & Biases SaaS.  
- Add CloudFront + Cognito for authenticated multi-tenant access.

---

## Expected Résumé Upgrades
1. **“Built and deployed retrieval-augmented chatbot on AWS (Lambda + pgvector) serving 50 req/s with <700 ms p95 latency.”**  
2. **“Implemented cost-aware multi-model agent (GPT-4o, Claude, Llama-3) with automated rollback via GitHub Actions and EKS blue/green deploys.”**  
3. **“Benchmarked GPU vs serverless LLM inference on AWS, reducing cost per 1k tokens 40 % while increasing throughput 15×.”**
