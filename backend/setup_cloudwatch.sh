#!/usr/bin/env bash
set -euo pipefail

echo "=== 1. Configuring Gunicorn log file and systemd service ==="
sudo touch /var/log/raktsetu.log
sudo chown ubuntu:ubuntu /var/log/raktsetu.log

sudo tee /etc/systemd/system/raktsetu.service > /dev/null <<'EOF'
[Unit]
Description=RaktSetu Blood Donor Platform Gunicorn API
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/Blood-Donor-Matching-Platform/backend
EnvironmentFile=/home/ubuntu/Blood-Donor-Matching-Platform/backend/.env
ExecStart=/home/ubuntu/Blood-Donor-Matching-Platform/backend/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:5000 --access-logfile - --error-logfile - "app:create_app()"
StandardOutput=append:/var/log/raktsetu.log
StandardError=append:/var/log/raktsetu.log
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable raktsetu
sudo systemctl restart raktsetu

echo "=== 2. Installing Amazon CloudWatch Agent ==="
TMP_DEB="/tmp/amazon-cloudwatch-agent.deb"
curl -fsSL "https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb" -o "${TMP_DEB}"
sudo dpkg -i -E "${TMP_DEB}"
rm -f "${TMP_DEB}"

echo "=== 3. Writing CloudWatch Agent configuration ==="
sudo mkdir -p /opt/aws/amazon-cloudwatch-agent/etc
sudo tee /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json > /dev/null <<'EOF'
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/raktsetu.log",
            "log_group_name": "/raktsetu/backend-api",
            "log_stream_name": "{instance_id}",
            "retention_in_days": 14
          }
        ]
      }
    }
  },
  "metrics": {
    "namespace": "RaktSetu/EC2",
    "append_dimensions": {
      "InstanceId": "${aws:InstanceId}"
    },
    "metrics_collected": {
      "mem": {
        "measurement": [
          "mem_used_percent"
        ]
      },
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "/"
        ]
      }
    }
  }
}
EOF

echo "=== 4. Starting Amazon CloudWatch Agent ==="
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

echo "=== 5. Service Status ==="
sudo systemctl status raktsetu --no-pager
sudo systemctl status amazon-cloudwatch-agent --no-pager
