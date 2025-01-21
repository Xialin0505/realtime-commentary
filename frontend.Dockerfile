# Use an official Node.js runtime as a parent image
FROM node:latest
# Set the working directory in the container
WORKDIR /usr/src/app
# Copy package.json and package-lock.json to the working directory
COPY package*.json ./
# Install application dependencies
RUN npm install
# Copy your application code into the container
COPY ./frontend .
# Expose a port your application will listen on
EXPOSE 3000

# Define the command to run your application
# CMD ["node", "server.js"]