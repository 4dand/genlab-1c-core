# =============================================================================
# GenLab-1C-Core — Автономный Docker-образ
# =============================================================================
# Сборка:   docker build -t genlab-1c-core .
# Запуск:   docker run --env-file .env genlab-1c-core run -c A -m gemini -t A1
# =============================================================================

FROM python:3.11-slim AS base

# Системные зависимости для matplotlib
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libfreetype6 \
        libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Зависимости (кэшируется отдельным слоем)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код проекта
COPY pyproject.toml main.py ./
COPY src/ src/
COPY configs/ configs/

# Рабочие директории (монтируются как volumes)
RUN mkdir -p raw_results code_outputs evaluations reports logs cache

# Непривилегированный пользователь
RUN groupadd -r genlab && useradd -r -g genlab -d /app genlab \
    && chown -R genlab:genlab /app
USER genlab

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
