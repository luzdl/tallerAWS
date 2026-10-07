FROM nginx:alpine

# DNS de la VPC de AWS; docker-compose lo sobrescribe con 127.0.0.11
ENV NGINX_RESOLVER=169.254.169.253

COPY index.html /usr/share/nginx/html/index.html
COPY default.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80
