# Nazara
### Operational Knowledge Intelligence System

> "We impose order on the chaos of system failures. Malfunctions persist only because we permit them — and they will cease when we decide they cease."

Nazara is an **Operational Knowledge Intelligence System** designed to ingest, unify, correlate and interpret operational signals from multiple sources. Its purpose is to turn scattered technical, customer, and incident data into a coherent, searchable, intelligent knowledge graph.

Nazara does **not** write to external systems. It **reads**, **understands**, **summarizes**, **embeds**, and **correlates**.

## What Nazara Does

### Ingests operational signals

- Customer-facing issues from Slack, Intercom, or similar
- Incidents from incident-management platforms
- Technical errors, anomalies, and signals from monitoring tools
- Engineering context from issue trackers

### Builds structured domain objects

- **CustomerCase** — symptoms affecting individual users
- **Incident** — system-wide or large-impact events
- **TechnicalEvent** — objective evidence from monitoring, logs or APM

### Enriches with AI

Nazara uses LLM providers to automatically:
- Generate concise summaries of incidents and cases
- Create embeddings for semantic similarity search
- Apply organizational context to improve enrichment quality

### Correlates everything

Nazara finds patterns such as:
- Multiple CustomerCases tied to the same underlying issue
- TechnicalEvents aligning with an incident timeline
- Recurring problems across time, systems, or services

### Enables semantic search

Using embeddings, Nazara can:
- Find similar cases or incidents
- Surface related technical events
- Discover historical patterns that resemble new failures

## Concepts

### CustomerCase

A customer-level operational symptom: what happened, when, to whom, and how it manifested.

### Incident

A platform-level failure or degradation with known or evolving impact.

### TechnicalEvent

Machine-generated evidence from monitoring, logs, APM or error trackers.

### TechnicalIssue

Aggregated pattern of related technical events for long-term trend analysis.

### DomainProfile

Organizational context that improves AI enrichment quality. Contains:
- **Categories** — how your organization classifies issues (billing, infrastructure, security)
- **Severities** — priority levels with ranking (critical, high, medium, low)
- **Systems** — services and infrastructure that can be affected
- **Glossary** — domain-specific terminology and definitions
- **Policies** — operational priorities that guide enrichment

### Enrichment Policy

Rules that control what gets enriched and when. Define target types, enrichment types (summary, embedding), and optional filters by category, severity, or service.

## Installation

```bash
pip install nazara
```

Add to your Django settings:

```python
import nazara

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# Configure Nazara (adds required apps, Celery settings, etc.)
nazara.configure(globals())
```

Run migrations:

```bash
python manage.py migrate
```

## Configuration

Nazara is configured via Django Admin at `/admin/`.

### 1. LLM Providers

Configure at least one LLM provider with API credentials:
- Select a model (OpenAI, Anthropic, etc.)
- Set the secret reference for API key
- Enable capabilities (summary, embedding)

### 2. Domain Profile

Create a Domain Profile with your organizational context:
- Add categories that match your issue classification
- Define severity levels with ranking
- Register systems and services
- Add glossary terms for domain-specific vocabulary

### 3. Enrichment Policies

Define what gets enriched:
- Select target type (Incident, CustomerCase, TechnicalIssue)
- Choose enrichment type (summary, embedding)
- Optionally filter by category, severity, or service

Mark the Domain Profile as **Active** to enable enrichment.

## Development

```bash
# Setup environment
cp .env.example .env

# Start services
docker compose up -d

# Run migrations
uv run python manage.py migrate

# Create admin user
uv run python manage.py createsuperuser

# Import default domain profile
uv run python manage.py import_domain_profile profiles/default_domain_profile.json --activate

# Run tests
uv run pytest tests/ --cov=src/nazara --cov-report=term-missing -v
```

## Docker

```bash
docker compose up -d
```
