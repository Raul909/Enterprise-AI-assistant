# Enterprise AI Knowledge Assistant (MCP-Based)

An enterprise-grade AI assistant that enables employees to query internal knowledge (documents, databases, GitHub, Jira) using natural language. The system uses **Model Context Protocol (MCP)** to safely orchestrate tools and **Retrieval-Augmented Generation (RAG)** for grounded AI responses.

---

## 🚀 Key Features

- **Natural Language Queries** - Ask questions in plain English about company data
- **Modern React UI** - Beautiful, professional interface with real-time chat
- **MCP Tool Orchestration** - Secure, auditable tool execution via Model Context Protocol
- **Multi-Source RAG** - Search documents, databases, GitHub, and Jira
- **Role-Based Access Control (RBAC)** - Fine-grained permissions per user role
- **Multi-LLM Support** - Use OpenAI GPT-4 or Anthropic Claude
- **Audit Logging** - Track all queries and tool executions
- **Conversation Memory** - Context-aware follow-up questions

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Optional)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   FastAPI Backend (8000)                     │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │   Auth   │  │ AI Orchestr. │  │   RAG Service          │ │
│  │  (JWT)   │  │  (LLM + MCP) │  │   (FAISS + Embeddings) │ │
│  └──────────┘  └──────┬───────┘  └────────────────────────┘ │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   MCP Server (3333)                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Tools: Documents | Database | GitHub | Jira            │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │
  ┌─────────────────────────┼─────────────────────────────────┐
  │                         │                                  │
  ▼                         ▼                                  ▼
┌──────────┐         ┌──────────────┐                  ┌────────────┐
│PostgreSQL│         │ Vector Store │                  │ External   │
│ (Users,  │         │   (FAISS)    │                  │ APIs       │
│  Logs)   │         │              │                  │(GitHub,    │
└──────────┘         └──────────────┘                  │ Jira)      │
                                                       └────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, Vite, Lucide Icons |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| **AI** | OpenAI GPT-4 / Anthropic Claude, SentenceTransformers, FAISS |
| **MCP** | Custom MCP Server with Tool Registry |
| **Auth** | JWT (python-jose), bcrypt |
| **Database** | PostgreSQL, Redis (caching) |
| **Infrastructure** | Docker, Docker Compose |

---

## 📁 Project Structure

```
enterprise-ai-assistant/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.jsx
│   │   │   ├── Login.css
│   │   │   ├── Chat.jsx
│   │   │   └── Chat.css
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST endpoints
│   │   │   ├── auth.py      # Authentication endpoints
│   │   │   ├── chat.py      # Chat/query endpoints
│   │   │   └── admin.py     # Admin endpoints
│   │   ├── core/            # Core utilities
│   │   │   ├── config.py    # Settings management
│   │   │   ├── security.py  # JWT & auth
│   │   │   └── logging.py   # Structured logging
│   │   ├── db/              # Database layer
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   │   ├── ai_orchestrator.py
│   │   │   ├── mcp_client.py
│   │   │   ├── rag_service.py
│   │   │   └── permission_service.py
│   │   └── main.py          # Application entry
│   └── requirements.txt
├── mcp-server/
│   ├── tools/               # Tool implementations
│   │   ├── document_tool.py
│   │   ├── database_tool.py
│   │   ├── github_tool.py
│   │   └── jira_tool.py
│   ├── server.py            # MCP server
│   ├── permissions.py       # RBAC
│   └── requirements.txt
├── vector-store/
│   ├── ingest.py            # Document ingestion
│   └── search.py            # Semantic search
├── docker/
│   ├── docker-compose.yaml
│   ├── backend.Dockerfile
│   └── mcp.Dockerfile
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API key or Anthropic API key

### 1. Clone and Configure

```bash
cd /home/raul/Downloads/enterprise-ai-assistant

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Run with Docker (Recommended)

```bash
cd docker
docker-compose up -d
```

This starts:

- PostgreSQL database on port 5432
- Redis cache on port 6379
- MCP Server on port 3333
- Backend API on port 8000

### 3. Run Locally (Development)

```bash
# Terminal 1: Start MCP Server
cd mcp-server
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 3333 --reload

# Terminal 2: Start Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3: Start Frontend
cd frontend
npm install
npm run dev
```

Access the UI at http://localhost:3000

---

## 📖 API Usage

### Authentication

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@company.com", "password": "securepass123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@company.com", "password": "securepass123"}'

# Response: {"access_token": "eyJ...", "token_type": "bearer", ...}
```

### Chat / Query

```bash
# Ask a question
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the company vacation policies?"}'

# Response includes answer, sources, and tools used
```

### Available Tools (by Role)

| Role | Tools |
|------|-------|
| **employee** | search_documents |
| **manager** | search_documents, query_database, search_jira, get_jira_ticket |
| **admin** | All tools including GitHub integration |

---

## ⚙️ Configuration

Key environment variables (see `.env.example` for full list):

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_PROVIDER` | LLM provider (openai/anthropic) | openai |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `JWT_SECRET_KEY` | Secret for JWT tokens | - |
| `MCP_SERVER_URL` | MCP server address | <http://localhost:3333> |

---

## 🔒 Security Features

- **JWT Authentication** with access/refresh tokens
- **Role-based Access Control** for tools and documents
- **SQL Injection Prevention** (SELECT-only queries)
- **Audit Logging** for all operations
- **Department-based Document Filtering**
- **Non-root Docker containers**

---

## 📊 Monitoring

- Health check: `GET /health`
- Audit logs: `GET /api/v1/admin/audit-logs` (admin only)
- System stats: `GET /api/v1/admin/stats` (admin only)

---

## 🧪 Testing

```bash
cd backend
pytest tests/ -v
```

---

## 📝 License

MIT License - See LICENSE file for details.
