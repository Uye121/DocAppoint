# ---- DEVELOPMENT/TEST STAGE ----
FROM node:24-alpine as development

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# ---- BUILD STAGE ----
FROM node:24-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# ---- PRODUCTION STAGE ----
FROM node:24-alpine AS production

# build argument
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

WORKDIR /app

# Copy only the built static files
COPY --from=builder /app/dist ./dist

# Install a lightweight static server
RUN npm install -g serve

EXPOSE 3000

# Use exec form for better signal handling
CMD ["serve", "-s", "dist", "-l", "3000"]