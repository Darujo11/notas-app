# Project Analysis: Analisador de Notas Fiscais (Streamlit PDF Analyzer)

---

## 📖 Overview

- **Purpose**: A Streamlit web application that extracts, cleans, aggregates, and reports fiscal invoice data from PDF files.  The user uploads a PDF containing tables of invoices, and the app produces interactive KPIs, filtered data tables, and downloadable TXT/PDF reports grouped by *Tomador de Serviços* (service taker) and *Contrato* (contract).
- **Primary Technologies**:
  - **Python 3.13** (slim image in Docker)
  - **Streamlit** – UI framework
  - **pdfplumber** – PDF table extraction
  - **pandas** – Data manipulation
  - **fpdf2** – PDF report generation
  - **Docker** – containerization for production deployment
- **Repository Layout**:
  - `app.py` – main Streamlit script (contains all logic).
  - `requirements.txt` – Python dependencies.
  - `Dockerfile` – builds a lightweight image.
  - `docker-compose.yml` – defines the service and Traefik labels.
  - `.gitignore` – excludes virtual‑env, caches, etc.
  - `SKILL.md` – documentation / skill definition (not directly used by the app).

---

## 🏗️ Architecture & Data Flow

```mermaid
flowchart TD
    A[User uploads PDF] --> B[process_pdf(file_bytes)]
    B --> C[DataFrame raw_df]
    C --> D[prepare_dataframe(df)]
    D --> E[Cleaned DataFrame]
    E -->|KPIs| F[Streamlit UI (metrics, tables)]
    E -->|Reports| G[generate_text_report]
    E -->|Reports| H[generate_pdf_report]
    G --> I[Download TXT]
    H --> J[Download PDF]
```

1. **Upload** – `st.file_uploader` receives the PDF bytes.
2. **Extraction** – `process_pdf` iterates over every page with `pdfplumber`, extracts tables, resolves multi‑page headers, and concatenates rows into `all_data`.
3. **Cleaning** – `prepare_dataframe`:
   - Renames columns to canonical names.
   - Converts monetary strings via `clean_currency`.
   - Extracts CNPJ, removes it from the service‑taker column.
   - Normalises *CONTRATO* values and fills missing contracts.
   - Strips note numbers.
4. **Reporting** – Two helpers:
   - `generate_text_report` builds a plain‑text summary.
   - `generate_pdf_report` builds a PDF using `FPDF`.
5. **UI** – Displays KPIs, a filtered data grid, a grouped summary table, and expanders for detailed rows.  Download buttons expose the generated reports.

---

## 🧩 Key Code Sections (app.py)

| Section | Description | Relevant Functions |
|---------|-------------|--------------------|
| **Configuration** | Sets page title, layout & icon. | `st.set_page_config` |
| **Utility** | Currency cleaning (BRL → float). | `clean_currency` |
| **PDF Processing** | Reads PDF, extracts tables, handles multi‑page headers. | `process_pdf` |
| **Data Preparation** | Normalises column names, extracts CNPJ, cleans values. | `prepare_dataframe` |
| **Report Generation** | Text and PDF report creators. | `generate_text_report`, `generate_pdf_report` |
| **Streamlit UI** | Title, uploader, progress, KPI cards, filtered view, download buttons, error handling. | Main script block after line 194 |

---

## 📦 Dependency Summary (`requirements.txt`)

```
streamlit
pandas
pdfplumber
openpyxl
fpdf2
```

- `openpyxl` is required by pandas when exporting to Excel (used implicitly if the user saves a DataFrame).
- `fpdf2` provides the `FPDF` class used for PDF report creation.

---

## 🐳 Dockerization

### Dockerfile
```Dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
```
- Builds a minimal image based on the official slim Python image.
- Installs exact dependencies from `requirements.txt`.
- Exposes the default Streamlit port (8501).
- Starts the app in headless mode for production.

### docker‑compose.yml
```yaml
version: '3.8'
services:
  app:
    image: notas-app:latest
    networks:
      - Monadanet
    deploy:
      replicas: 1
      labels:
        - "traefik.enable=true"
        - "traefik.docker.network=Monadanet"
        - "traefik.http.routers.notas-app.entrypoints=websecure"
        - "traefik.http.routers.notas-app.rule=Host(`notas.autozapx.com`)"
        - "traefik.http.routers.notas-app.tls.certresolver=letsencryptresolver"
        - "traefik.http.services.notas-app.loadbalancer.server.port=8501"

networks:
  Monadanet:
    external: true
```
- Uses an **external** Docker network (`Monadanet`) that is shared with Traefik.
- Adds all the necessary Traefik labels for HTTPS routing to `notas.autozapx.com`.

---

## ⚙️ Setup & Execution Guide

### 1️⃣ Local Development (quick test)
```bash
# Clone / navigate to the project folder (already done)
python -m pip install -r requirements.txt   # install deps
python -m streamlit run app.py               # start UI on http://localhost:8501
```
*If `python -m streamlit` fails, ensure the correct Python interpreter (3.13) is being used.*

### 2️⃣ Containerized Deployment
```bash
# Build the image (run once or after code changes)
docker compose build

# Start the stack (Traefik must already be running on the host)
docker compose up -d
```
- The service will be reachable at **https://notas.autozapx.com** (provided DNS points to the VPS IP and Traefik is configured with Let’s Encrypt).

### 3️⃣ Stopping / Cleaning
```bash
docker compose down   # stop containers
docker rmi notas-app   # optionally remove the image
```

---

## 🚀 Extensibility Ideas

- **Authentication** – add `streamlit-authenticator` to restrict access.
- **Database storage** – persist extracted data in SQLite/PostgreSQL for historical analysis.
- **Batch processing** – expose a REST endpoint (FastAPI) that receives PDFs and returns JSON reports.
- **Internationalisation** – externalise Portuguese strings to support multiple languages.
- **Unit tests** – create pytest suites for `clean_currency`, `prepare_dataframe`, and report generators.

---

## 📂 File Map (with links)

- [app.py](file:///c:/Users/CLIENTE/OneDrive/Documentos/Skill/Dados/analista-dados/analista-dados/app.py)
- [requirements.txt](file:///c:/Users/CLIENTE/OneDrive/Documentos/Skill/Dados/analista-dados/analista-dados/requirements.txt)
- [Dockerfile](file:///c:/Users/CLIENTE/OneDrive/Documentos/Skill/Dados/analista-dados/analista-dados/Dockerfile)
- [docker-compose.yml](file:///c:/Users/CLIENTE/OneDrive/Documentos/Skill/Dados/analista-dados/analista-dados/docker-compose.yml)
- [.gitignore](file:///c:/Users/CLIENTE/OneDrive/Documentos/Skill/Dados/analista-dados/analista-dados/.gitignore)

---

*Generated automatically by Antigravity – a powerful coding assistant.*
