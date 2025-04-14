# Stage 1: Build the SvelteKit application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package.json and lock file
# Copy these first to leverage Docker layer caching
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Set the API URL build argument (can be overridden)
ARG VITE_API_URL=http://localhost:5000
ENV VITE_API_URL=${VITE_API_URL}

# Build the application
# Ensure your build script is correctly named in package.json (usually "build")
RUN npm run build

# Stage 2: Serve the application using a lightweight server
# Using a simple Node server with 'sirv-cli' as an example
# Alternatively, use Nginx or another static server
FROM node:18-alpine

WORKDIR /app

# Install sirv for serving static files
# RUN npm install -g sirv-cli

# Copy built assets from the builder stage
# Adjust the source path if your SvelteKit adapter outputs elsewhere (e.g., adapter-static)
COPY --from=builder /app/build .

# Copy the package.json from the builder stage to ensure "type": "module" is set
COPY --from=builder /app/package.json .

# Expose the port the app runs on (default for SvelteKit node-adapter is 3000)
EXPOSE 3000

# Command to run the server built by adapter-node
# The entrypoint is usually index.js in the build output directory
CMD [ "node", "index.js" ] 