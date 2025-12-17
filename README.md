# JuniorDebug Backend

A FastAPI-based backend for the JuniorDebug code analysis tool.

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

4. Run the server:

```bash
python -m uvicorn app.main:app --reload
```

Or use the provided batch file:

```bash
run_server.bat
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /` - Health check
- `GET /health` - Health check
- `POST /analyze` - Analyze code

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key
- `ANTHROPIC_API_KEY` - Your Anthropic API key
- `SUPABASE_URL` - Supabase project URL (future use)
- `SUPABASE_KEY` - Supabase API key (future use)

## Deploying to Render

You can host the backend on Render as a separate service. This repo includes a `render.yaml` at the repository root which configures a service that points to the `backend/` folder.

Render settings (used by `render.yaml`):

- Service `path`: `backend`
- `buildCommand`: `pip install -r backend/requirements.txt`
- `startCommand`: `gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

Steps to deploy:

1. Push this repository to GitHub.
2. In Render, create a new Web Service and connect your GitHub repo.
3. Set the service path to `backend` (the `render.yaml` already points there).
4. Add required environment variables (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) in the Render dashboard under Environment.
5. Deploy. Render will run the build and start commands.

Notes:

- Render provides a `PORT` environment variable at runtime — the Procfile and `render.yaml` use `$PORT`.
- For local testing we use `uvicorn` during development; Render uses Gunicorn with Uvicorn worker for production concurrency.

Additional CORS note:

- If your frontend is hosted on Vercel (or another host), set a `FRONTEND_URL` environment variable in Render to your frontend origin (for example `https://your-site.vercel.app`). The backend will allow requests from that origin. Do not include a trailing slash.
