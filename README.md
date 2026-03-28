<h1 align="center">Image Search Engine</h1>

<p align="center">
  <strong>AI-powered photo search with natural language understanding</strong>
</p>

<p align="center">
  Find photos by describing them. Search <em>"sunset at the beach with friends"</em> or <em>"birthday party at home"</em> instantly across your entire library.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776ab?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Next.js-14-000000?logo=next.js&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Qdrant-vector%20search-dc382d" alt="Qdrant">
  <img src="https://img.shields.io/badge/version-2.0.0-blue" alt="Version">
</p>

<p align="center">
  <a href="#-the-problem">Problem</a> &bull;
  <a href="#-architecture">Architecture</a> &bull;
  <a href="#-features">Features</a> &bull;
  <a href="#-quick-start">Quick Start</a> &bull;
  <a href="#-api-reference">API</a> &bull;
  <a href="#-project-structure">Structure</a>
</p>

---

## The Problem

Your photo library has thousands of images. Finding a specific one is painful:

- **Filename search?** Useless. `IMG_4392.jpg` tells you nothing.
- **Date-based browsing?** Hope you remember when it was taken.
- **Manual tagging?** Nobody has time for that.

You remember _what's in the photo_, not when you took it or what you named it.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Next.js Frontend                             │
│              Dashboard  ·  Gallery  ·  People  ·  Events             │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼───────────────────────────────────────────┐
│                        FastAPI Backend                                │
│                                                                      │
│  ┌─────────────┐  ┌──────────────────────────────────────────────┐   │
│  │  API Routes  │  │           Processing Pipeline                │   │
│  │  /images     │  │                                              │   │
│  │  /search     │  │  Ingestion ──► Understanding ──► Enrichment  │   │
│  │  /faces      │  │                                              │   │
│  │  /events     │  │  ┌─────────┐ ┌────────┐ ┌──────────────┐   │   │
│  │  /stats      │  │  │  CLIP   │ │ YOLO   │ │   Gemini AI  │   │   │
│  └─────────────┘  │  │Embedding│ │Objects │ │  Captioning  │   │   │
│                    │  └─────────┘ └────────┘ └──────────────┘   │   │
│                    │  ┌─────────┐ ┌────────┐ ┌──────────────┐   │   │
│                    │  │DeepFace │ │  OCR   │ │    Scene     │   │   │
│                    │  │  Faces  │ │  Text  │ │Classification│   │   │
│                    │  └─────────┘ └────────┘ └──────────────┘   │   │
│                    └──────────────────────────────────────────────┘   │
└──────────┬───────────────────────────────────┬───────────────────────┘
           │                                   │
  ┌────────▼────────┐                 ┌────────▼────────┐
  │   PostgreSQL    │                 │     Qdrant      │
  │   Metadata &    │                 │  Vector Search  │
  │   Relations     │                 │   Embeddings    │
  └─────────────────┘                 └─────────────────┘
```

**Six AI models work together at ingestion time:**

| Model | Purpose | Output |
|-------|---------|--------|
| **OpenCLIP** (ViT-B-32) | Semantic image understanding | 512-dim embeddings |
| **YOLOv8** | Object detection | Bounding boxes + labels |
| **DeepFace** (ArcFace) | Face detection & recognition | Face clusters + identities |
| **Tesseract OCR** | Text extraction from images | Extracted text |
| **Gemini AI** | Image captioning & scene description | Natural language captions |
| **Scene Classifier** | Scene & emotion classification | Scene type, mood, aesthetics |

---

## Features

| Feature | Description |
|---------|-------------|
| **Semantic Search** | Search by meaning. _"cozy evening"_ finds candlelit dinners |
| **Face Recognition** | Auto-clusters faces, search by person name |
| **Object Detection** | Knows what's in the photo — people, cars, dogs, furniture |
| **OCR Search** | Find text in images — receipts, signs, documents |
| **Event Grouping** | Auto-groups photos into events by time and location |
| **Smart Captions** | AI-generated descriptions for every image |
| **Scene Classification** | Indoor/outdoor, mood, aesthetics scoring |
| **Location & Temporal** | GPS reverse geocoding, time-of-day classification |
| **Modern UI** | Next.js dashboard with gallery, people, and event views |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- [Gemini API key](https://aistudio.google.com/app/apikey) (for captioning)

### 1. Start Infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL (port 5434) and Qdrant (port 6333).

### 2. Backend Setup

```bash
cd backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your GEMINI_API_KEY and IMAGE_STORAGE_PATH

uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://imagesearch:imagesearch@localhost:5434/imagesearch` | PostgreSQL connection |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant vector DB |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `IMAGE_STORAGE_PATH` | `~/Pictures` | Root path to scan for photos |
| `CLIP_MODEL` | `ViT-B-32` | OpenCLIP model variant |
| `CLIP_PRETRAINED` | `openai` | OpenCLIP pretrained weights |

---

## API Reference

Base URL: `http://localhost:8000/api`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/images/ingest` | Ingest images from a directory |
| `GET` | `/images/` | List images with pagination |
| `GET` | `/images/{id}` | Get image details |
| `POST` | `/search/` | Semantic search with natural language |
| `GET` | `/faces/persons` | List recognized people |
| `POST` | `/faces/persons/{id}/name` | Name a recognized person |
| `GET` | `/events/` | List auto-detected events |
| `GET` | `/stats/` | Dashboard statistics |

---

## Project Structure

```
image_search/
├── docker-compose.yml           # PostgreSQL + Qdrant
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifespan
│   │   ├── config.py            # Pydantic settings
│   │   ├── api/routes/          # REST endpoints
│   │   ├── db/                  # SQLAlchemy models + repo
│   │   ├── schemas/             # Pydantic request/response
│   │   ├── services/            # Business logic + workers
│   │   ├── search/              # Query parsing + ranking
│   │   ├── vector/              # Qdrant client + store
│   │   └── pipeline/
│   │       ├── orchestrator.py  # Multi-stage pipeline
│   │       ├── ingestion.py     # File discovery + hashing
│   │       ├── understanding/   # CLIP, YOLO, faces, OCR, captions
│   │       └── enrichment/      # Events, location, classification
│   ├── alembic/                 # Database migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/                 # Next.js pages (App Router)
│       ├── components/          # Reusable UI components
│       ├── hooks/               # Data fetching hooks
│       └── lib/                 # API client
└── data/                        # Local data (gitignored)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS |
| **Backend** | FastAPI, SQLAlchemy, Pydantic |
| **Database** | PostgreSQL 16 |
| **Vector Search** | Qdrant |
| **ML / Vision** | OpenCLIP, YOLOv8, DeepFace, Tesseract, Gemini |
| **Infra** | Docker Compose |

---

<p align="center">
  Built with FastAPI + Next.js + Qdrant
</p>
