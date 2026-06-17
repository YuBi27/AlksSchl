FROM python:3.13-slim

WORKDIR /app

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ /app/api/
RUN touch /app/api/__init__.py

COPY alembic.ini /app/alembic.ini
COPY migrations/ /app/migrations/
COPY tests/ /app/tests/
COPY pytest.ini /app/pytest.ini

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
