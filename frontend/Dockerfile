# ---- DEVELOPMENT/TEST STAGE ----
FROM node:24-alpine as development

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# ---- PRODUCTION STAGE ----
FROM node:24-alpine as production

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

COPY . .

RUN npm run build

RUN npm install -g serve
EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]