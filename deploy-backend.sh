#!/bin/bash
# AWS Backend Deployment Script for VibeAgent Forge

set -e

echo "🚀 Starting VibeAgent Forge Backend Deployment to AWS..."

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="vibeagent-infrastructure"
ECR_REPO_NAME="vibeagent-backend"
ECS_CLUSTER_NAME="vibeagent-cluster"
ECS_SERVICE_NAME="vibeagent-backend-service"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Check AWS CLI
echo -e "${YELLOW}[1/10] Checking AWS CLI...${NC}"
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI found${NC}"

# Step 2: Create CloudFormation Stack
echo -e "${YELLOW}[2/10] Creating AWS Infrastructure with CloudFormation...${NC}"
aws cloudformation create-stack \
    --stack-name $STACK_NAME \
    --template-body file://aws/cloudformation-template.yml \
    --capabilities CAPABILITY_IAM \
    --region $AWS_REGION \
    --tags Key=Project,Value=VibeAgentForge || echo "Stack already exists or creation started"

echo "Waiting for stack creation (this takes ~10-15 minutes)..."
aws cloudformation wait stack-create-complete \
    --stack-name $STACK_NAME \
    --region $AWS_REGION

echo -e "${GREEN}✓ Infrastructure created${NC}"

# Step 3: Get Stack Outputs
echo -e "${YELLOW}[3/10] Getting infrastructure details...${NC}"
VPC_ID=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`VPCId`].OutputValue' \
    --output text \
    --region $AWS_REGION)

DB_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
    --output text \
    --region $AWS_REGION)

REDIS_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue' \
    --output text \
    --region $AWS_REGION)

ALB_DNS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
    --output text \
    --region $AWS_REGION)

echo -e "${GREEN}✓ Got infrastructure details${NC}"

# Step 4: Create ECR Repository
echo -e "${YELLOW}[4/10] Creating ECR repository...${NC}"
aws ecr create-repository \
    --repository-name $ECR_REPO_NAME \
    --region $AWS_REGION 2>/dev/null || echo "Repository already exists"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

echo -e "${GREEN}✓ ECR repository ready${NC}"

# Step 5: Login to ECR
echo -e "${YELLOW}[5/10] Logging in to ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

echo -e "${GREEN}✓ Logged in to ECR${NC}"

# Step 6: Build Docker Image
echo -e "${YELLOW}[6/10] Building Docker image...${NC}"
cd backend
docker build -t $ECR_REPO_NAME:latest .
cd ..

echo -e "${GREEN}✓ Docker image built${NC}"

# Step 7: Tag and Push Image
echo -e "${YELLOW}[7/10] Pushing image to ECR...${NC}"
docker tag $ECR_REPO_NAME:latest $ECR_URI:latest
docker push $ECR_URI:latest

echo -e "${GREEN}✓ Image pushed to ECR${NC}"

# Step 8: Create Secrets in Secrets Manager
echo -e "${YELLOW}[8/10] Creating secrets...${NC}"

# Get database password
DB_PASSWORD=$(aws secretsmanager get-secret-value \
    --secret-id vibeagent/database-password \
    --query SecretString \
    --output text \
    --region $AWS_REGION | jq -r .password)

# Create DATABASE_URL secret
aws secretsmanager create-secret \
    --name vibeagent/database-url \
    --secret-string "postgresql+asyncpg://postgres:${DB_PASSWORD}@${DB_ENDPOINT}:5432/vibeagent" \
    --region $AWS_REGION 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id vibeagent/database-url \
    --secret-string "postgresql+asyncpg://postgres:${DB_PASSWORD}@${DB_ENDPOINT}:5432/vibeagent" \
    --region $AWS_REGION

# Create REDIS_URL secret
aws secretsmanager create-secret \
    --name vibeagent/redis-url \
    --secret-string "redis://${REDIS_ENDPOINT}:6379/0" \
    --region $AWS_REGION 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id vibeagent/redis-url \
    --secret-string "redis://${REDIS_ENDPOINT}:6379/0" \
    --region $AWS_REGION

# Create SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)
aws secretsmanager create-secret \
    --name vibeagent/secret-key \
    --secret-string "$SECRET_KEY" \
    --region $AWS_REGION 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id vibeagent/secret-key \
    --secret-string "$SECRET_KEY" \
    --region $AWS_REGION

# Create OPENROUTER_API_KEY (you need to set this)
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo -e "${RED}ERROR: OPENROUTER_API_KEY environment variable not set${NC}"
    echo "Please set it: export OPENROUTER_API_KEY=your-key"
    exit 1
fi

aws secretsmanager create-secret \
    --name vibeagent/openrouter-key \
    --secret-string "$OPENROUTER_API_KEY" \
    --region $AWS_REGION 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id vibeagent/openrouter-key \
    --secret-string "$OPENROUTER_API_KEY" \
    --region $AWS_REGION

echo -e "${GREEN}✓ Secrets created${NC}"

# Step 9: Update Task Definition with correct values
echo -e "${YELLOW}[9/10] Registering ECS task definition...${NC}"

# Update task definition JSON with actual values
cat aws/ecs-task-definition.json | \
    sed "s|YOUR_ACCOUNT_ID|$ACCOUNT_ID|g" | \
    sed "s|YOUR_ECR_REGISTRY|${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com|g" | \
    sed "s|us-east-1|${AWS_REGION}|g" > /tmp/ecs-task-definition.json

aws ecs register-task-definition \
    --cli-input-json file:///tmp/ecs-task-definition.json \
    --region $AWS_REGION

echo -e "${GREEN}✓ Task definition registered${NC}"

# Step 10: Create or Update ECS Service
echo -e "${YELLOW}[10/10] Creating ECS service...${NC}"

# Get subnet IDs and security group from stack
SUBNET_1=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=${VPC_ID}" "Name=tag:Name,Values=*Public-Subnet-1" \
    --query 'Subnets[0].SubnetId' \
    --output text \
    --region $AWS_REGION)

SUBNET_2=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=${VPC_ID}" "Name=tag:Name,Values=*Public-Subnet-2" \
    --query 'Subnets[0].SubnetId' \
    --output text \
    --region $AWS_REGION)

SECURITY_GROUP=$(aws ec2 describe-security-groups \
    --filters "Name=vpc-id,Values=${VPC_ID}" "Name=group-name,Values=*ECSSecurityGroup*" \
    --query 'SecurityGroups[0].GroupId' \
    --output text \
    --region $AWS_REGION)

TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups \
    --names production-tg \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text \
    --region $AWS_REGION)

# Create ECS service
aws ecs create-service \
    --cluster $ECS_CLUSTER_NAME \
    --service-name $ECS_SERVICE_NAME \
    --task-definition vibeagent-backend \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$SECURITY_GROUP],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=$TARGET_GROUP_ARN,containerName=vibeagent-backend,containerPort=8000" \
    --region $AWS_REGION 2>/dev/null || \
aws ecs update-service \
    --cluster $ECS_CLUSTER_NAME \
    --service $ECS_SERVICE_NAME \
    --force-new-deployment \
    --region $AWS_REGION

echo -e "${GREEN}✓ ECS service created/updated${NC}"

# Final Output
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Backend API URL: ${GREEN}http://${ALB_DNS}${NC}"
echo -e "API Docs: ${GREEN}http://${ALB_DNS}/docs${NC}"
echo -e "Health Check: ${GREEN}http://${ALB_DNS}/health${NC}"
echo ""
echo -e "${YELLOW}Save this URL for Vercel frontend deployment!${NC}"
echo ""
