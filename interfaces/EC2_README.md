EC2 deployment quickstart

1) Build and push the image to ECR
   - aws ecr create-repository --repository-name cs474-explainers (if not exists)
   - docker build -t cs474-explainers:latest .
   - docker tag cs474-explainers:latest <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/cs474-explainers:latest
   - aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com
   - docker push <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/cs474-explainers:latest

2) Launch an EC2 instance
   - Instance type: t3.large or t3.xlarge (or Graviton t4g.* if ARM is acceptable)
   - AMI: Amazon Linux 2 or Ubuntu
   - Disk: 50–100 GB gp3
   - Security Group: allow inbound TCP on 80 (or chosen port) from your users; allow SSH from admin IPs

3) Install Docker on the instance
   - Amazon Linux 2:
       sudo yum update -y
       sudo amazon-linux-extras install docker -y
       sudo service docker start
       sudo usermod -aG docker ec2-user
   - Ubuntu:
       sudo apt update && sudo apt install -y docker.io
       sudo usermod -aG docker ubuntu

4) Pull and run the container
   - Login to ECR:
       aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com
   - Pull:
       docker pull <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/cs474-explainers:latest
   - Run (maps container 8080 to host 80 and persists outputs):
       docker run -d --restart unless-stopped -p 80:8080 -v /home/ec2-user/out:/app/out <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/cs474-explainers:latest

5) Access
   - Visit http://<EC2_PUBLIC_IP> in your browser.
   - PDFs and .tex outputs will appear under /home/ec2-user/out on the host.

Notes
 - Streamlit is bound to 0.0.0.0:8080 in the image; adjust the host port mapping as needed.
 - For HTTPS, place an ALB or a reverse proxy (e.g., Caddy/Traefik) in front, or terminate TLS on the instance.
 - Restrict the Security Group to known CIDRs if possible.
