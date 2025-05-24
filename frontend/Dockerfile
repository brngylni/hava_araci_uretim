FROM node:18-alpine AS builder

WORKDIR /app


COPY package*.json ./

# Bağımlılıkları kur
RUN npm ci

# Tüm proje dosyalarını kopyala
COPY . .

RUN npm run build


FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx portunu aç
EXPOSE 80

# Nginx'i başlat
CMD ["nginx", "-g", "daemon off;"]