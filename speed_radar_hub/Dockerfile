ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    nginx \
    sqlite

# Create app directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/
COPY run.sh /

# Copy nginx config
COPY rootfs/ /

# Make run script executable
RUN chmod a+x /run.sh

# Expose port
EXPOSE 8103

CMD ["/run.sh"]
