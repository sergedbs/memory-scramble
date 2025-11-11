FROM python:3.13-slim-bookworm

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy server code
COPY app/ /app/app/

# Copy boards
COPY boards/ /app/boards/

# Copy public content to serve
COPY public/ /app/public/

# Expose port
EXPOSE 8080

# Run server 
CMD ["python3", "-u", "-m", "app.server"]
