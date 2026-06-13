FROM python:3.12-slim

# Install uv (needed to run, but packages come from copied venv)
RUN pip install uv

WORKDIR /app

# Copy venv FROM HOST (all packages already downloaded, baked into image layer)
# This runs ONCE on --build, then layer is cached forever
COPY .venv/ /root/.venv/

# Copy source
COPY . .

# All packages now in /root/.venv/ — run directly, no download
CMD ["/root/.venv/bin/python", "-m", "uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8001"]