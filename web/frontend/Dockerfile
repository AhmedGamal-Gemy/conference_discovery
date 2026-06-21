# ── Stage 1: install dependencies ─────────────────────────────────────
FROM node:20-slim AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --quiet

# ── Stage 2: development ────────────────────────────────────────────────
FROM node:20-slim AS dev
WORKDIR /app

# Copy installed node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV VITE_API_PROXY_TARGET=http://backend:8001
ENV VITE_HOST=0.0.0.0
ENV VITE_PORT=5173

EXPOSE 5173

CMD ["sh", "-c", "npm run dev -- --host 0.0.0.0 --port $VITE_PORT"]