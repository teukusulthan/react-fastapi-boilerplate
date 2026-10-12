# syntax=docker/dockerfile:1
# Production image for apps/web: Vite build -> static files served by unprivileged nginx.
#
#   docker build -t app-web apps/web
#   docker run --rm -p 8080:8080 -e BACKEND_URL=http://host.docker.internal:8020 app-web
#
# VITE_* variables are baked in at build time (env/.env.production if present, or the
# --build-arg values declared below); there is no runtime injection. Only BACKEND_URL
# (the /api/v1/apps/ upstream) is configurable at runtime.

# ---------------------------------------------------------------------------- build
FROM node:24-alpine AS build
WORKDIR /app
ENV CI=true

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund

COPY . .
# Optional build-time overrides (unset args are not exported, so src/config/env.ts defaults
# apply): docker build --build-arg VITE_APP_NAME="My App" apps/web
ARG VITE_APP_NAME
ARG VITE_APP_DESCRIPTION
ARG VITE_API_BASE_URL
ARG VITE_MAPBOX_TOKEN
RUN npm run build

# -------------------------------------------------------------------------- runtime
# Same nginx alpine image, preconfigured to run as a non-root user (uid 101) on :8080.
FROM nginxinc/nginx-unprivileged:stable-alpine AS runtime

# Upstream for /api/v1/apps/ (see nginx.conf); resolvers come from /etc/resolv.conf.
ENV BACKEND_URL=http://backend:8020 \
    NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1

COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1:8080/ || exit 1
