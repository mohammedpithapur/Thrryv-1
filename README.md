 # Thrryv

Thrryv is a community-driven knowledge platform that blends AI-assisted credibility analysis with human annotations. Users can post claims, attach evidence, and crowd-evaluate accuracy and context. The system scores clarity, originality, relevance, and evidentiary value to surface high-quality content while keeping the user experience lightweight and social.

## Why it matters

- Helps communities reduce misinformation through transparent evidence and context.
- Combines machine scoring with human feedback for more nuanced outcomes.
- Encourages constructive debate and boosts impactful contributions.

## Core capabilities

- Post claims with evidence (images and videos).
- AI analysis for clarity, context, relevance, and evidentiary value.
- Credibility and impact scoring with visible signals.
- Annotation system with support, contradict, and context labels.
- Feed filters for recent, debated, and uncertain content.

## Tech stack

- Frontend: React, Tailwind CSS, Recharts
- Backend: FastAPI, Python

## Project structure

- backend/: FastAPI app, AI evaluation logic, and tests
- frontend/: React app, UI components, and pages
- memory/: Product requirements and planning notes
- test_reports/: Test artifacts and results

## Getting started

### Backend

1. Create a virtual environment and install dependencies:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Start the API server:

```bash
python server.py
```

### Frontend

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Start the dev server:

```bash
npm start
```

## Environment variables

Create a .env in frontend/ with:

```bash
REACT_APP_BACKEND_URL=http://127.0.0.1:8000
```

## API overview

- GET /api/claims: list posts
- POST /api/claims: create a post
- GET /api/claims/{id}: get post details
- POST /api/claims/{id}/annotations: add annotation

## Testing

Backend tests:

```bash
cd backend
pytest
```

## CI

GitHub Actions runs backend tests and a frontend build on pushes and pull requests to `main`.

## Roadmap

- Authentication hardening and role-based moderation
- Search improvements with semantic matching
- Scalable storage and media processing pipeline

## License

MIT
