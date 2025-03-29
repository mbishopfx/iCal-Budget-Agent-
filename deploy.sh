#!/bin/bash

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-venv python3-pip nginx

# Create application directory
sudo mkdir -p /var/www/ical-agent
sudo chown -R $USER:$USER /var/www/ical-agent

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Copy systemd service file
sudo cp ical-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ical-agent
sudo systemctl start ical-agent

# Configure Nginx
sudo tee /etc/nginx/sites-available/ical-agent << EOF
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /var/www/ical-agent/static;
    }
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/ical-agent /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t
sudo systemctl restart nginx

# Install Certbot for SSL
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com  # Replace with your domain 