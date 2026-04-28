#!/bin/bash
set -euxo pipefail

apt-get update
apt-get install -y docker.io awscli
systemctl enable --now docker
usermod -aG docker ubuntu || true

IMAGE_URI="${IMAGE_URI:-<ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/cs474-explainers:latest}"
HOST_OUT="/home/ubuntu/out"
mkdir -p "$HOST_OUT"

aws ecr get-login-password --region "${REGION:-<REGION>}" | docker login --username AWS --password-stdin "$(echo "$IMAGE_URI" | cut -d/ -f1)"

docker pull "$IMAGE_URI"
docker run -d --restart unless-stopped -p 80:8080 -v "${HOST_OUT}:/app/out" "$IMAGE_URI"
