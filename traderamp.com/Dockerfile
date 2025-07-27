# Multi-stage build for TradeRamp static website
FROM nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Remove default nginx config
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx-site.conf /etc/nginx/conf.d/default.conf

# Copy static website files
COPY index.html /usr/share/nginx/html/
COPY robots.txt /usr/share/nginx/html/
COPY sitemap.xml /usr/share/nginx/html/
COPY assets/ /usr/share/nginx/html/assets/
# Images are already in assets/images/

# Copy HubSpot setup documentation (optional)
COPY HUBSPOT-*.md /usr/share/nginx/html/docs/
COPY README.md /usr/share/nginx/html/docs/

# Set proper permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

# Create a simple health check endpoint
RUN echo "OK" > /usr/share/nginx/html/health

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Run nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]