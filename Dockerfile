FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml README.md alembic.ini ./
COPY alembic ./alembic
COPY narra ./narra
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN pip install --no-cache-dir . && chmod +x /app/docker-entrypoint.sh
EXPOSE 8000
CMD ["/app/docker-entrypoint.sh"]
