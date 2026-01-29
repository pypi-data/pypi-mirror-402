## Django Tech Stack Template

Define your technical stack below. This serves as a reference for all team members and helps maintain consistency across the project.

## ⚠️ REQUIRED TOOLS

**All Django applications MUST use:**
1. **Poetry** - For dependency management (NO pip/requirements.txt)
2. **Docker** - For containerization and deployment (NO manual deployments)

These are non-negotiable requirements for consistency and reproducibility across all environments.

---

### Core Framework
- **Application Framework:** Django 6+ (LTS recommended)
- **Language/Runtime:** Python 3.13+
- **Package Manager:** **Poetry** (REQUIRED - manages dependencies via pyproject.toml)
- **Environment Management:** pyenv
- **Containerization:** **Docker + docker-compose** (REQUIRED)

### API Layer
- **REST API:** Django REST Framework (DRF) 3.14+
- **API Documentation:** drf-spectacular (OpenAPI/Swagger)

### Database & Storage
- **Primary Database:** PostgreSQL 16+
- **ORM:** Django ORM (built-in)
- **Migrations:** Django migrations (built-in)
- **Database Tools:**
  - psycopg2-binary (PostgreSQL adapter)
- **File Storage:**
  - Development: Django FileSystemStorage
  - Production: django-storages (S3, GCS, Azure)
- **Caching:** Redis 7+ (django-redis)

### Frontend (if applicable)
- **Template Engine:** Django Templates
- **Static Files:** WhiteNoise (production serving)
- **CSS Framework:** Tailwind CSS or Bootstrap 5
- **JavaScript:**
  - Alpine.js (lightweight)
  - HTMX (hypermedia approach)
  - React/Vue (for SPA features)
- **Build Tools:** Vite or Webpack

### Background Jobs & Async Tasks
- **Task Queue:** Celery 5.3+
- **Message Broker:** Redis or RabbitMQ
- **Scheduler:** Celery Beat (periodic tasks)

### Authentication & Authorization
- **User Authentication:** Django built-in auth system
- **API Authentication:**
  - djangorestframework-simplejwt (JWT)
  - Token Authentication (DRF built-in)
- **Permissions:** Django permissions + DRF permissions

### Testing & Quality
- **Test Framework:** pytest-django
- **Test Tools:**
  - factory-boy (test data factories)
  - faker (fake data generation)
  - coverage.py (code coverage)
  - pytest-cov (pytest coverage plugin)
- **API Testing:** DRF APIClient
- **Code Formatting:**
  - black (code formatter)
  - isort (import sorting)
- **Linting:**
  - flake8 (style guide enforcement)
  - pylint (code analysis)
  - mypy (type checking)
- **Pre-commit Hooks:** pre-commit (runs formatters/linters)

### Developer Tools
- **Debugging:**
  - django-debug-toolbar (development)
  - django-extensions (shell_plus, runserver_plus)
- **Environment Variables:**
  - .env file management

### Monitoring & Logging
- **Error Tracking:** Sentry
- **Application Monitoring:**
  - New Relic or Datadog
  - Prometheus + Grafana (open source)
- **Logging:**
  - Python logging module (Django configured)
  - opentelemetry
- **Performance Monitoring:**
  - Django Silk (development)
  - django-querycount (query monitoring)

### Deployment & Infrastructure
- **Containerization:** **Docker + docker-compose** (REQUIRED)
  - All applications must be containerized
  - Multi-stage builds for optimization
  - docker-compose for local development
- **Web Server:**
  - Gunicorn (WSGI server)
  - Uvicorn (ASGI server for async)
- **Reverse Proxy:** Nginx
- **CI/CD:**
  - GitHub Actions (recommended)
- **Database Hosting:**
  - Managed PostgreSQL (RDS, DigitalOcean, Render)

### Security
- **HTTPS:** Let's Encrypt (certbot)
- **Security Headers:** django-csp, django-cors-headers
- **Rate Limiting:** django-ratelimit or DRF throttling
- **Secrets Management:**
  - Environment variables
  - AWS Secrets Manager
  - HashiCorp Vault

### Event-Driven Architecture
- **Message Queue:** RabbitMQ
- **Event Store:** PostgreSQL (Outbox pattern)
- **Streaming:** Apache Kafka (django-kafka)
- **WebSockets:** Django Channels (ASGI)

### Common Django Packages
**Essential:**
- django-environ (environment variables)
- psycopg2-binary (PostgreSQL)
- djangorestframework (REST API)
- celery[redis] (background tasks)
- gunicorn (WSGI server)
- whitenoise (static files)

**Recommended:**
- drf-spectacular (API docs)
- django-redis (caching)
- django-cors-headers (CORS)
- django-filter (filtering)
- Pillow (image processing)
- python-dateutil (date utilities)

**Development:**
- pytest-django (testing)
- factory-boy (test factories)
- black (formatting)
- isort (import sorting)
- flake8 (linting)
- django-debug-toolbar (debugging)
- ipython (enhanced shell)

### Version Control
- **VCS:** Git
- **Repository:** GitHub
- **Branching Strategy:** Git Flow
- **Commit Convention:** Conventional Commits

### Documentation
- **Project Docs:** README.md (Markdown)
- **API Docs:** drf-spectacular (auto-generated)
- **Code Docs:** Google-style docstrings
- **Architecture:** Mermaid diagram

---

## Poetry Configuration (REQUIRED)

### Installation
```bash
curl -sSL https://install.python-poetry.org | python3 -
# Or: pipx install poetry
```

### Essential Commands
```bash
poetry install              # Install all dependencies
poetry install --only main  # Production only
poetry add package-name     # Add dependency
poetry add --group dev pkg  # Add dev dependency
poetry update               # Update all packages
poetry shell                # Activate virtual env
```

### Minimal pyproject.toml
```toml
[tool.poetry.dependencies]
python = "^3.13"
django = "^5.0"
djangorestframework = "^3.14"
psycopg2-binary = "^2.9"
celery = {extras = ["redis"], version = "^5.3"}
django-outbox-pattern = "^1.0"

[tool.poetry.group.dev.dependencies]
pytest-django = "^4.5"
black = "^23.12"
isort = "^5.13"
django-debug-toolbar = "^4.2"
```

### Best Practices
- Always commit `poetry.lock` to version control
- Use `^` for compatible updates (e.g., `^5.0` allows 5.x but not 6.0)
- Never mix Poetry with pip/requirements.txt
- Let Poetry manage virtual environments

**Full Poetry docs:** https://python-poetry.org/docs/

---

## Docker Configuration (REQUIRED)

### Key Files
```
Dockerfile              # Multi-stage build (builder + runtime)
docker-compose.yml      # Development services
.dockerignore           # Build exclusions
```

### Dockerfile Structure
Use **multi-stage build** with Poetry:
- Stage 1: Builder (installs dependencies)
- Stage 2: Runtime (copies artifacts, runs as non-root user)

**Key points:**
- Install Poetry in builder stage only
- Copy packages from builder to runtime
- Run as non-root user (appuser)
- Include health check
- Set CMD to gunicorn

**Full example Dockerfile:** See Django Docker best practices documentation

### docker-compose.yml (Essential Services)
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: myproject
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  rabbitmq:
    image: rabbitmq:3-management-alpine
    command: bash -c "rabbitmq-plugins enable rabbitmq_stomp && rabbitmq-server"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
      - rabbitmq

  celery_worker:
    build: .
    command: celery -A myproject worker
    depends_on:
      - redis

  outbox_publisher:
    build: .
    command: python manage.py publish
    depends_on:
      - rabbitmq

volumes:
  postgres_data:
```

### Essential Commands
```bash
# Setup
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Development
docker-compose logs -f web              # View logs
docker-compose exec web python manage.py shell  # Django shell
docker-compose exec web pytest          # Run tests

# After dependency changes
poetry add package-name
docker-compose build web
docker-compose up -d web

# Cleanup
docker-compose down     # Stop all
docker-compose down -v  # Stop and remove volumes
```

### Best Practices
- Multi-stage builds for smaller images
- Non-root user for security
- Health checks for all services
- Use `.dockerignore` to exclude unnecessary files
- Environment variables via `.env` file
- Volume mounts for development (hot reload)

**Detailed examples:** Search "Django Docker multi-stage build" for comprehensive tutorials

---

## Summary: Required Tooling

✅ **Poetry** - Manages all Python dependencies
✅ **Docker** - Containerizes application and all services
✅ **docker-compose** - Orchestrates multi-container development

**No exceptions:** All Django applications must use Poetry for dependency management and Docker for containerization. This ensures consistency across development, testing, and production environments.
