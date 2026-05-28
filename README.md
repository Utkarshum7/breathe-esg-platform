# Breathe ESG — ESG Data Ingestion + Analyst Review Platform

> **Internship Assignment · Breathe**
> A full-stack platform for ingesting corporate greenhouse gas emission data from heterogeneous enterprise sources, normalising it to comparable base units, and enabling ESG analysts to review, flag, and cryptographically lock emission records in an immutable audit ledger.

---

## Live Deployment

| Service | URL |
| :--- | :--- |
| **Frontend (Vercel)** | _Add your Vercel URL after deployment_ |
| **Backend API (Render)** | _Add your Render URL after deployment_ |
| **Django Admin** | _Backend URL_ + `/admin/` |
| **DRF Browsable API** | _Backend URL_ + `/api/` |

---

## Architecture Overview

```
breathe-esg-intern/
├── backend/                    # Django 6 + DRF — ingestion engine & REST API
│   ├── apps/
│   │   ├── core/               # Organization, DataSource domain models
│   │   ├── ingestion/          # UploadBatch, EmissionRecord, parsers, API views
│   │   │   └── services/       # Strategy-pattern service layer (pure Python)
│   │   │       ├── base_parser.py
│   │   │       ├── sap_parser.py
│   │   │       ├── utility_parser.py
│   │   │       ├── travel_parser.py
│   │   │       ├── validator.py
│   │   │       ├── normalizer.py
│   │   │       └── ingestion_service.py
│   │   └── audit/              # AuditTrail — append-only immutable ledger
│   ├── config/                 # Django settings, URLs, WSGI
│   └── requirements.txt
├── frontend/                   # React 18 + Vite 5 + Tailwind CSS 3
│   └── src/
│       ├── components/         # StatusBadge, FilterBar, ApprovalModal
│       ├── pages/              # DashboardPage, UploadPage, RecordsPage
│       └── services/api.js     # Centralised Axios API client
├── docs/                       # Design documentation
│   ├── MODEL.md                # Schema, multi-tenancy, normalization
│   ├── DECISIONS.md            # Architectural choices and assumptions
│   ├── TRADEOFFS.md            # Deliberate omissions and rationale
│   └── SOURCES.md              # Data format research and limitations
├── sample_data/                # Prototype files for local testing
│   ├── sap_fuel_sample.csv
│   ├── utility_electricity_sample.csv
│   └── corporate_travel_sample.json
├── render.yaml                 # Render Infrastructure-as-Code (one-click deploy)
└── .gitignore
```

### Data Pipeline Flow

```
Source File  →  Upload API  →  Parser (Strategy)  →  Validator  →  Normaliser
     ↓
EmissionRecord (DRAFT / SUSPICIOUS / FAILED)
     ↓
Analyst Review Dashboard
     ↓
Approval (transaction.atomic)  →  AuditTrail (immutable ledger lock)
```

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| Backend Framework | Django 6.0 + Django REST Framework 3.17 |
| Database (dev) | SQLite |
| Database (prod) | PostgreSQL (Render managed) |
| Auth | Django session auth + DRF browsable API |
| Static Files | WhiteNoise 6.9 |
| Frontend | React 18 + Vite 5 |
| Styling | Tailwind CSS 3.4 |
| HTTP Client | Axios 1.x |
| Deployment — Backend | Render (Web Service + PostgreSQL) |
| Deployment — Frontend | Vercel |

---

## Local Development Setup

### Prerequisites

- Python 3.12+ (available via WSL on Windows)
- Node.js 18+ and npm
- Git

### Backend

```bash
# 1. Navigate to backend
cd backend

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # Linux/macOS/WSL
# OR: .\venv\Scripts\activate     # Windows CMD

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env — no changes needed for local SQLite dev

# 5. Run database migrations
python manage.py migrate

# 6. Create a superuser for Django Admin access
python manage.py createsuperuser

# 7. Start the development server
python manage.py runserver
# → API available at http://localhost:8000/api/
# → Admin panel at  http://localhost:8000/admin/
```

### Frontend

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install Node dependencies
npm install

# 3. Configure environment variables
cp .env.example .env
# .env already points to http://localhost:8000 — no changes needed locally

# 4. Start the Vite development server
npm run dev
# → Dashboard available at http://localhost:5173
```

### Running the Test Suite

```bash
# From the backend/ directory (WSL)
wsl ./venv/bin/python manage.py test --verbosity=2

# Expected output:
# Ran 24 tests in ~30s
# OK
```

---

## Seeding Initial Data (Required for Upload Workflow)

Before uploading files, create at least one `Organization` and one `DataSource` per type in Django Admin:

1. Open `http://localhost:8000/admin/`
2. Sign in with your superuser credentials
3. Under **Core → Organizations**, create an organisation (e.g. *Acme Corp*)
4. Under **Core → Data Sources**, create three records:
   - Name: `SAP Fuel Feed` · Source Type: `SAP_FUEL` · Organization: *Acme Corp*
   - Name: `Utility Feed` · Source Type: `UTILITY_ELECTRICITY` · Organization: *Acme Corp*
   - Name: `Travel Feed` · Source Type: `CORP_TRAVEL` · Organization: *Acme Corp*

Then upload the sample files from `sample_data/` in the Upload Center.

---

## API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/organizations/` | List all tenant organisations |
| `GET` | `/api/datasources/` | List all data source configurations |
| `POST` | `/api/upload/sap/` | Ingest SAP Fuel CSV |
| `POST` | `/api/upload/utility/` | Ingest Utility Electricity CSV |
| `POST` | `/api/upload/travel/` | Ingest Corporate Travel JSON |
| `GET` | `/api/batches/` | List all upload batches |
| `GET` | `/api/batches/{id}/` | Retrieve single batch detail |
| `GET` | `/api/records/` | List emission records (supports filters) |
| `GET` | `/api/records/{id}/` | Retrieve single emission record |
| `POST` | `/api/records/{id}/approve/` | Approve and lock a record |

**Record query parameters:** `?batch=<uuid>`, `?data_source=<uuid>`, `?status=DRAFT`, `?suspicious=true`

---

## Design Documentation

| Document | Purpose |
| :--- | :--- |
| [docs/MODEL.md](docs/MODEL.md) | Schema design, multi-tenancy, audit logic, normalization ratios |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Architectural choices, parser strategies, PM assumptions |
| [docs/TRADEOFFS.md](docs/TRADEOFFS.md) | Three deliberate omissions and technical justifications |
| [docs/SOURCES.md](docs/SOURCES.md) | Data format research, sample realism, parser limitations |

---

## Deployment

### One-Click Backend Deploy to Render

> The `render.yaml` at the repo root is a Render Blueprint that provisions the Django web service **and** the managed PostgreSQL database together.

1. Push the repository to GitHub
2. Open [dashboard.render.com](https://dashboard.render.com) → **New → Blueprint**
3. Connect the GitHub repository
4. Render auto-reads `render.yaml` — review the plan and click **Apply**
5. Wait ~3 minutes for the build to complete
6. In the Render dashboard, open the web service shell and run:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
7. Note your service URL (e.g. `https://breathe-esg-api.onrender.com`)

**Required environment variables** (set in Render dashboard if not using Blueprint):

| Variable | Value |
| :--- | :--- |
| `SECRET_KEY` | Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `breathe-esg-api.onrender.com` |
| `DATABASE_URL` | Auto-injected by Render Blueprint from managed PostgreSQL |
| `CORS_ALLOW_ALL_ORIGINS` | `False` |
| `CORS_ALLOWED_ORIGINS` | `https://your-app.vercel.app` |

### Frontend Deploy to Vercel

1. Open [vercel.com](https://vercel.com) → **Add New → Project**
2. Import the GitHub repository
3. Set **Root Directory** to `frontend`
4. Vercel auto-detects Vite — accept the defaults
5. Add environment variable:
   - `VITE_API_URL` = `https://breathe-esg-api.onrender.com`
6. Click **Deploy**
7. Note your Vercel URL and update `CORS_ALLOWED_ORIGINS` in Render with it

---

## Screenshots

_Add screenshots of each page after local or production deployment._

| Page | Screenshot |
| :--- | :--- |
| ESG Command Dashboard | _Paste screenshot here_ |
| Upload Center (SAP CSV ingest) | _Paste screenshot here_ |
| Review Ledger (suspicious row highlighted) | _Paste screenshot here_ |
| Approval Modal (analyst reasoning) | _Paste screenshot here_ |
| Django Admin | _Paste screenshot here_ |

---

## Demo Credentials

_For reviewer access — update before submission._

| Role | Username | Password |
| :--- | :--- | :--- |
| Django Admin / Analyst | `admin` | _Set when running `createsuperuser`_ |

---

## Project Phases Completed

| Phase | Description | Status |
| :--- | :--- | :---: |
| Phase 1 | Monorepo setup, Django + React + Vite + Tailwind scaffolding | ✅ |
| Phase 2 | Domain models: Organization, DataSource, UploadBatch, EmissionRecord, AuditTrail | ✅ |
| Phase 3 | Ingestion engine: Strategy parsers, Validator, Normaliser, IngestionService | ✅ |
| Phase 4 | DRF REST API: upload endpoints, ledger views, approval workflow, 24 tests | ✅ |
| Phase 5 | React analyst dashboard: Dashboard, Upload Center, Review Ledger, Approval UX | ✅ |
| Release | Production settings, Render + Vercel deployment config, documentation | ✅ |
