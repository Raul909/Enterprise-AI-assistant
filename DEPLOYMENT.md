# Deployment Guide <!-- id: 0 -->

This guide explains how to deploy the Enterprise AI Assistant to [Render](https://render.com) using the included `render.yaml` Blueprint.

## Local Development <!-- id: 1 -->

Before deploying, test locally:

```bash
# Quick start (from project root)
./start-frontend.sh

# Or manually:
cd frontend
npm install
cp .env.example .env
npm run dev
```

Ensure backend is running on port 8000. Frontend will be available at http://localhost:3000.

## Prerequisites <!-- id: 2 -->

1. A [Render](https://render.com) account.
2. The project pushed to a Git repository (GitHub/GitLab).
3. API Keys for OpenAI or Anthropic.

## Backend Deployment (API & MCP Server) <!-- id: 2 -->

The project is configured with a `render.yaml` Blueprint which automatically sets up:

- **PostgreSQL Database** (`enterprise-ai-db`)
- **Redis Cache** (`enterprise-ai-redis`)
- **Backend API Service** (`enterprise-ai-backend`)
- **MCP Server Service** (`enterprise-ai-mcp`)

### Steps: <!-- id: 3 -->

1. **Dashboard**: Go to your Render Dashboard.
2. **New Blueprint**: Click **New +** and select **Blueprint**.
3. **Connect Repo**: Connect the repository containing this code.
4. **Service Name**: Give your blueprint a name (e.g., `enterprise-ai`).
5. **Environment Variables**: Render will ask you to provide values for variables defined with `sync: false` in `render.yaml`:
   - `OPENAI_API_KEY`: Your key from OpenAI (if using OpenAI).
   - `ANTHROPIC_API_KEY`: Your key from Anthropic (if using Claude).
   - `AI_PROVIDER`: Set to `openai` or `anthropic` (default is `openai`).
6. **Apply**: Click **Apply**. Render will deploy all services.

> **Note**: The `database` and `redis` services are free types in the configuration, but you can upgrade them in the Render dashboard if needed for production.

### Automatic Configuration <!-- id: 4 -->

The `render.yaml` automatically handles:

- Injecting the `DATABASE_URL` into the backend.
- Injecting the `REDIS_URL` into the backend.
- Injecting the `MCP_SERVER_URL` into the backend (using internal networking).
- Generating a secure `JWT_SECRET_KEY`.

## Frontend Deployment <!-- id: 5 -->

The project includes a modern React frontend in the `frontend/` directory.

### Deploy to Render (Static Site) <!-- id: 6 -->

1. **Push Frontend to Git**: Ensure the `frontend/` directory is in your repository.

2. **Create Static Site**:
   - Go to Render Dashboard → **New +** → **Static Site**
   - Connect your repository
   - Configure:
     - **Name**: `enterprise-ai-frontend`
     - **Root Directory**: `frontend`
     - **Build Command**: `npm install && npm run build`
     - **Publish Directory**: `frontend/dist`

3. **Environment Variables**:
   Add to the Static Site settings:
   ```
   VITE_API_URL=https://your-backend-url.onrender.com/api/v1
   ```
   Replace with your actual backend URL from step 1.

4. **Deploy**: Click **Create Static Site**. Render will build and deploy your frontend.

### Configure CORS <!-- id: 7 -->

Update your backend service environment variables in Render:

```
CORS_ORIGINS=https://your-frontend-url.onrender.com
```

Or for multiple origins (comma-separated):
```
CORS_ORIGINS=https://your-frontend-url.onrender.com,http://localhost:3000
```

### Alternative: Deploy to Vercel/Netlify <!-- id: 8 -->

**Vercel:**
```bash
cd frontend
npm install -g vercel
vercel --prod
```

**Netlify:**
```bash
cd frontend
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

Both platforms offer free tiers and automatic HTTPS.

## Troubleshooting <!-- id: 9 -->

- **Build Failures**: Check the logs in the Render dashboard. Ensure `docker/backend.Dockerfile` paths are correct relative to the repo root.
- **Database Connection**: Ensure the backend service has the `DATABASE_URL` environment variable (Render Blueprints do this automatically).
- **CORS Errors**: If your frontend cannot talk to the backend, add your frontend URL to the `CORS_ORIGINS` environment variable in the Backend Service settings (comma-separated).
- **Frontend API Connection**: Verify `VITE_API_URL` in frontend environment variables points to the correct backend URL.
- **Authentication Issues**: Ensure JWT tokens are being stored and sent correctly. Check browser console for errors.
