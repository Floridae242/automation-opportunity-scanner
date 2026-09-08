FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 AOS_ROOT=/app AOS_API_ROOT=/app
WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app
COPY apps/api/requirements-dev.lock ./requirements.lock
RUN pip install --no-deps -r requirements.lock
COPY apps/api/pyproject.toml ./pyproject.toml
COPY apps/api/src ./src
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/migrations ./migrations
COPY prompts ./prompts
COPY schemas ./schemas
RUN pip install --no-deps . && chown -R app:app /app

USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"
CMD ["uvicorn", "aos_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
