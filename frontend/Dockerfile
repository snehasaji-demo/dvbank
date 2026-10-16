FROM node:16-alpine

WORKDIR /app

# Add node user to root group
RUN addgroup node root

# Copy package.json first
COPY package.json ./

# Install dependencies and create package-lock.json
RUN npm install

# Copy the rest of the application
COPY . .\n
# Set correct permissions
RUN chown -R node:node /app

# Switch to node user
USER node

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD node -e "require('http').get('http://localhost:3000/', (res) => { if (res.statusCode !== 200) process.exit(1); }).on('error', () => process.exit(1));"

CMD ["npm", "start"]