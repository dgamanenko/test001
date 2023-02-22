FROM python:3.9-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required dependencies
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_14.x | bash - && \
    apt-get install -y nodejs && \
    pip install --no-cache-dir -r requirements.txt && \
    npm install -g kustomize@4.1.2

# Set the environment variables
ENV KUBECONFIG /app/config.yaml

# Expose the port 8080
EXPOSE 8080

# Run the controller
CMD [ "python", "./controller/controller.py" ]