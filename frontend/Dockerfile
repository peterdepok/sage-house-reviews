FROM node:18-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Ensure vite is in the path
ENV PATH /app/node_modules/.bin:$PATH

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
