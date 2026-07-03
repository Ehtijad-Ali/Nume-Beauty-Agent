# ============================================================
# NUMÉ Frontend — Vite dev server in a container
# (use a multi-stage build for production later)
# ============================================================

FROM node:20-alpine

ENV CI=true
WORKDIR /app

# Install deps
COPY package.json package-lock.json* ./
RUN npm install

# Copy source
COPY . .

EXPOSE 5173

# Vite dev server, listening on all interfaces so the host can reach it
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
