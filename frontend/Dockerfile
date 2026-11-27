FROM node:20-alpine

RUN sed -i 's#http://#https://#g' /etc/apk/repositories && apk upgrade --no-cache

WORKDIR /app

# Add node user to root group
RUN addgroup node root

# Copy package.json first
COPY package.json ./ 

# Install dependencies and create package-lock.json
RUN npm install

# Copy the rest of the application
COPY . .

# Set correct permissions
RUN chown -R node:node /app

# Switch to node user
USER node

EXPOSE 3000

CMD ["npm", "start"]