# ---- DEVELOPMENT/TEST STAGE ----
FROM python:3.11-slim as development

# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1 \
#Prevents Python from buffering stdout and stderr
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root --with dev
    
RUN mkdir -p /app/media/speciality /app/media/healthcare_providers

# Copy project
COPY . .

# ---- PRODUCTION STAGE ----
FROM python:3.11-slim as production

# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1 \
#Prevents Python from buffering stdout and stderr
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root --without dev
    
RUN mkdir -p /app/media/speciality /app/media/healthcare_providers

# Copy project
COPY . .

EXPOSE 8000

CMD sh -c "python manage.py migrate && python manage.py seed_providers && gunicorn api.wsgi:application --bind 0.0.0.0:8000"