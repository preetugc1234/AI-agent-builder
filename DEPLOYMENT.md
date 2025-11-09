# VibeAgent Forge - Deployment Guide

Complete deployment guide for both frontend (Vercel) and backend (AWS Free Tier).

## 📋 Prerequisites

- AWS Account (Free Tier eligible)
- Vercel Account
- OpenRouter API Key (for NVIDIA Nemotron)
- Git installed
- Docker installed (for local development)

## 🚀 Quick Start - Local Development

### 1. Clone Repository

```bash
git clone https://github.com/preetugc1234/AI-agent-builder.git
cd AI-agent-builder
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
cp .env.example .env.local
```

### 4. Run with Docker Compose

```bash
# From root directory
docker-compose up -d

# Access:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

## ☁️ Production Deployment

### Part 1: AWS Backend Deployment (Free Tier)

#### Step 1: Setup AWS Infrastructure

```bash
# Install AWS CLI
aws configure

# Create CloudFormation stack
aws cloudformation create-stack \
  --stack-name vibeagent-infrastructure \
  --template-body file://aws/cloudformation-template.yml \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

#### Step 2: Create ECR Repository

```bash
# Create ECR repository for backend
aws ecr create-repository \
  --repository-name vibeagent-backend \
  --region us-east-1

# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

#### Step 3: Build and Push Docker Image

```bash
cd backend

# Build image
docker build -t vibeagent-backend .

# Tag image
docker tag vibeagent-backend:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/vibeagent-backend:latest

# Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/vibeagent-backend:latest
```

#### Step 4: Create Secrets in AWS Secrets Manager

```bash
# Database URL
aws secretsmanager create-secret \
  --name vibeagent/database-url \
  --secret-string "postgresql+asyncpg://postgres:PASSWORD@RDS_ENDPOINT:5432/vibeagent"

# Redis URL
aws secretsmanager create-secret \
  --name vibeagent/redis-url \
  --secret-string "redis://REDIS_ENDPOINT:6379/0"

# Secret Key
aws secretsmanager create-secret \
  --name vibeagent/secret-key \
  --secret-string "YOUR_SECRET_KEY"

# OpenRouter API Key
aws secretsmanager create-secret \
  --name vibeagent/openrouter-key \
  --secret-string "YOUR_OPENROUTER_API_KEY"
```

#### Step 5: Create ECS Service

```bash
# Update task definition with your ECR image URL
# Edit aws/ecs-task-definition.json

# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://aws/ecs-task-definition.json

# Create ECS service
aws ecs create-service \
  --cluster vibeagent-cluster \
  --service-name vibeagent-backend-service \
  --task-definition vibeagent-backend \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[SUBNET_ID_1,SUBNET_ID_2],securityGroups=[SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=TARGET_GROUP_ARN,containerName=vibeagent-backend,containerPort=8000"
```

#### Step 6: Get Backend URL

```bash
# Get ALB DNS name
aws elbv2 describe-load-balancers \
  --names production-alb \
  --query 'LoadBalancers[0].DNSName' \
  --output text

# Your backend will be available at: http://YOUR_ALB_DNS
```

### Part 2: Vercel Frontend Deployment

#### Step 1: Push to GitHub

```bash
# From root directory
git add .
git commit -m "Initial deployment"
git push origin main
```

#### Step 2: Deploy to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your GitHub repository
4. Configure project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

#### Step 3: Add Environment Variables in Vercel

In Vercel project settings, add:

```
NEXT_PUBLIC_API_URL=http://YOUR_ALB_DNS
NEXT_PUBLIC_WS_URL=ws://YOUR_ALB_DNS
```

#### Step 4: Deploy

Click "Deploy" - Vercel will automatically build and deploy your frontend.

## 🔧 Post-Deployment Setup

### 1. Setup Database

```bash
# Connect to RDS instance and run migrations
# Install psql client first

psql -h YOUR_RDS_ENDPOINT -U postgres -d vibeagent

# The FastAPI app will auto-create tables on first run
```

### 2. Test Deployment

```bash
# Test backend health
curl http://YOUR_ALB_DNS/health

# Test frontend
curl https://YOUR_VERCEL_URL
```

### 3. Setup Custom Domain (Optional)

#### For Backend (API):
1. Create Route53 hosted zone
2. Add A record pointing to ALB
3. Create ACM certificate
4. Update ALB listener to use HTTPS

#### For Frontend:
1. In Vercel project settings → Domains
2. Add your custom domain
3. Follow Vercel's DNS configuration instructions

## 🔒 Security Checklist

- [ ] Enable AWS WAF on ALB
- [ ] Enable RDS encryption at rest
- [ ] Enable CloudWatch logging
- [ ] Setup AWS CloudTrail
- [ ] Enable MFA on AWS account
- [ ] Rotate secrets regularly
- [ ] Use AWS Secrets Manager for all credentials
- [ ] Enable VPC Flow Logs
- [ ] Setup AWS Backup for RDS
- [ ] Configure CORS properly

## 💰 Cost Optimization (Free Tier)

**AWS Free Tier includes:**
- ✅ EC2: 750 hours/month (t2.micro or t3.micro)
- ✅ RDS: 750 hours/month (db.t2.micro or db.t3.micro)
- ✅ ElastiCache: 750 hours/month (cache.t3.micro)
- ✅ S3: 5GB storage
- ✅ CloudWatch: Basic monitoring
- ✅ ALB: 750 hours/month

**To stay within free tier:**
1. Use single ECS task (not auto-scaled)
2. Use t3.micro instances only
3. Don't enable Multi-AZ for RDS
4. Use S3 for static assets
5. Monitor AWS Cost Explorer daily

## 📊 Monitoring

### CloudWatch Alarms

```bash
# CPU Utilization alarm
aws cloudwatch put-metric-alarm \
  --alarm-name vibeagent-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

### Logs

```bash
# View ECS task logs
aws logs tail /ecs/vibeagent-backend --follow
```

## 🔄 CI/CD Setup (Optional)

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Build and push to ECR
        run: |
          aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${{ secrets.ECR_REGISTRY }}
          docker build -t vibeagent-backend backend/
          docker tag vibeagent-backend:latest ${{ secrets.ECR_REGISTRY }}/vibeagent-backend:latest
          docker push ${{ secrets.ECR_REGISTRY }}/vibeagent-backend:latest

      - name: Update ECS service
        run: |
          aws ecs update-service --cluster vibeagent-cluster --service vibeagent-backend-service --force-new-deployment
```

## 🐛 Troubleshooting

### Backend not starting
```bash
# Check ECS task logs
aws ecs describe-tasks --cluster vibeagent-cluster --tasks TASK_ID

# Check CloudWatch logs
aws logs tail /ecs/vibeagent-backend --follow
```

### Database connection issues
```bash
# Test RDS connectivity from ECS task
aws ecs execute-command --cluster vibeagent-cluster --task TASK_ID --command "nc -zv RDS_ENDPOINT 5432"
```

### WebSocket not connecting
- Ensure ALB supports WebSocket (it does by default)
- Check security group rules allow traffic
- Verify CORS settings in backend

## 📚 Additional Resources

- [AWS Free Tier Details](https://aws.amazon.com/free/)
- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)

## 🆘 Support

If you encounter issues:
1. Check CloudWatch logs
2. Verify all environment variables are set
3. Ensure security groups allow traffic
4. Check AWS service quotas
5. Review ECS task definition

For questions: [Open an issue](https://github.com/preetugc1234/AI-agent-builder/issues)
