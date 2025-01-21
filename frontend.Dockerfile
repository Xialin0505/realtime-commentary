# Use an official Node.js runtime as a parent image
FROM node:latest
# Set the working directory in the container
WORKDIR /usr/src/app

# Copy your application code into the container
COPY ./frontend .

# Install application dependencies
RUN npm install -g npm@11.0.0
RUN npm install --force

# Expose a port your application will listen on
EXPOSE 3000

# Define the command to run your application
# CMD ["npm", "run", "start"]