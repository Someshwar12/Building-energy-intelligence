FROM node:22-alpine AS builder

WORKDIR /app

COPY apps/api/package*.json ./
RUN npm ci

COPY apps/api/ ./
COPY data ./data

RUN npm run build


FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/package*.json ./
RUN npm ci --omit=dev

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/data ./data

EXPOSE 4000

CMD ["npm", "start"]