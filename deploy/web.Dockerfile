# Web (app PWA) — build static webapp (Vite) rồi nginx phục vụ + proxy /api → api container.
# Build với context = gốc repo:  docker build -f deploy/web.Dockerfile .
# ---- Stage 1: build dist ----
FROM node:22-alpine AS build
WORKDIR /src
RUN npm install -g pnpm@10
# Cài deps trước (cache theo lockfile)
COPY webapp/package.json webapp/pnpm-lock.yaml ./webapp/
RUN cd webapp && pnpm install --frozen-lockfile
COPY webapp ./webapp
RUN cd webapp && pnpm build

# ---- Stage 2: nginx phục vụ ----
FROM nginx:alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/webapp/dist /usr/share/nginx/html
