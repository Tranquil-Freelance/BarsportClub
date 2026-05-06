# Next.js development Dockerfile for xPalermoStat frontend
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies (including dev dependencies)
RUN npm ci

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Set environment variable for development
ENV NODE_ENV=development

# Start development server
CMD ["npm", "run", "dev"]