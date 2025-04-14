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
RUN npm install -g sirv-cli

# Copy built assets from the builder stage
# Adjust the source path if your SvelteKit adapter outputs elsewhere (e.g., adapter-static)
COPY --from=builder /app/build .

# Expose the port the app runs on (default for SvelteKit node-adapter is 3000)
EXPOSE 3000

# Command to run the server
# The entrypoint might differ based on your adapter (e.g., node-adapter uses 'node index.js')
# This example uses sirv to serve the built static assets
# CMD [ "node", "index.js" ] # Typical for node-adapter
CMD [ "sirv", ".", "--host", "0.0.0.0", "--port", "3000" ] # Example using sirv for static adapter output 