FROM node:22-alpine

WORKDIR /app

# Install dependencies first so this layer is cached unless package*.json changes
COPY package*.json ./
RUN npm install

# Source is bind-mounted over this in docker-compose for live editing;
# this copy just makes the image runnable standalone too.
COPY . .

EXPOSE 5173

# Re-run npm install at startup if node_modules is missing or incomplete.
# This guards against the bind mount in docker-compose hiding the
# node_modules that were installed during the image build (e.g. on a
# fresh checkout, or after the anonymous volume gets reset).
CMD sh -c "[ -x node_modules/.bin/vite ] || npm install; npm run dev -- --host 0.0.0.0"