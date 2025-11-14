# 🚀 GitHub Actions Auto-Deploy (No Docker Desktop Needed!)

## ✅ What This Does

Every time you `git push` to main branch:
- ✅ GitHub builds Docker image in the cloud
- ✅ Pushes to AWS ECR automatically
- ✅ Deploys to AWS ECS automatically
- ✅ **NO Docker Desktop required!**
- ✅ Completely FREE!

---

## 📋 Setup Steps

### **Step 1: Setup AWS Infrastructure** (Run ONCE)

1. Open Command Prompt
2. Run:
```bash
cd C:\Users\mt\AI-agent-builder
setup-infrastructure.bat
```

This creates:
- VPC, Subnets, Security Groups
- RDS PostgreSQL Database
- ElastiCache Redis
- Application Load Balancer
- ECS Cluster
- All AWS Secrets

**Takes: 10-15 minutes**

---

### **Step 2: Add Secrets to GitHub** (Run ONCE)

1. **Go to GitHub Secrets:**
   - Open: https://github.com/preetugc1234/AI-agent-builder/settings/secrets/actions

2. **Click "New repository secret"** and add these 3 secrets:

   **Secret 1:**
   - Name: `AWS_ACCESS_KEY_ID`
   - Value: (Get from credentials.txt file)

   **Secret 2:**
   - Name: `AWS_SECRET_ACCESS_KEY`
   - Value: (Get from credentials.txt file)

   **Secret 3:**
   - Name: `OPENROUTER_API_KEY`
   - Value: (Get from credentials.txt file)

---

### **Step 3: Push to GitHub to Deploy!**

```bash
git add .
git commit -m "Enable auto-deploy with GitHub Actions"
git push origin main
```

**That's it!** GitHub Actions will automatically:
1. Build Docker image
2. Push to AWS ECR
3. Deploy to ECS

**Watch live:** https://github.com/preetugc1234/AI-agent-builder/actions

---

## 🎯 How It Works

### **Traditional Way (With Docker Desktop):**
```
You: Edit code → git push
Your Computer: Build Docker → Push to AWS → Deploy
Problem: Need Docker Desktop installed
```

### **GitHub Actions Way (No Docker Desktop):**
```
You: Edit code → git push
GitHub Cloud: Build Docker → Push to AWS → Deploy
Benefit: Everything happens in cloud!
```

---

## 📊 Deployment Status

After pushing code, check:
- **GitHub Actions:** https://github.com/preetugc1234/AI-agent-builder/actions
- **Backend Health:** http://YOUR-ALB-DNS/health
- **API Docs:** http://YOUR-ALB-DNS/docs

---

## 🔄 Daily Workflow

```bash
# 1. Make changes to backend code
code backend/app/api/agents.py

# 2. Commit and push
git add .
git commit -m "Added new feature"
git push origin main

# 3. That's it! Auto-deploys in 5-10 minutes
```

---

## 💰 Cost

- **GitHub Actions:** FREE (2,000 minutes/month for private repos)
- **AWS Infrastructure:** FREE (12 months free tier)
- **Total Cost:** $0 for first year!

After 12 months: ~$25-30/month for AWS

---

## 🛠️ Troubleshooting

**Deployment failed?**
1. Check: https://github.com/preetugc1234/AI-agent-builder/actions
2. Click on failed workflow
3. See error logs
4. Fix and push again

**Need to redeploy without code changes?**
```bash
git commit --allow-empty -m "Trigger deploy"
git push origin main
```

**Want to deploy only backend changes?**
- The workflow only triggers when `backend/` folder changes
- Frontend changes won't trigger backend deployment

---

## 📝 Files Created

- `.github/workflows/deploy.yml` - GitHub Actions workflow
- `setup-infrastructure.bat` - AWS infrastructure setup
- `BACKEND_URL.txt` - Your backend URL (auto-generated)

---

## ✅ Advantages Over Docker Desktop

| Feature | Docker Desktop | GitHub Actions |
|---------|----------------|----------------|
| Build Speed | Depends on your PC | Fast cloud servers |
| Installation | Need to install | Nothing to install |
| Disk Space | Uses 2-5 GB | No local space used |
| Cost | Free (paid for teams) | Free forever |
| Auto-deploy | Manual | Automatic on push |

---

## 🎉 You're Done!

Your backend now auto-deploys on every `git push`!

**No Docker Desktop. No manual builds. Just code and push!**
