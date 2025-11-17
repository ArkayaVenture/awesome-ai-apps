# Streamlit Cloud Deployment Guide

## 🚀 Deploying Multi-Agent SRE Bot to Streamlit Community Cloud

This guide explains how to deploy the Multi-Agent SRE Bot to Streamlit Cloud and configure Kubernetes cluster access.

## 📋 Prerequisites

1. **Streamlit Cloud Account**: Sign up at https://streamlit.io/cloud
2. **GitHub Repository**: Your code must be in a GitHub repository
3. **Kubernetes Cluster**: Accessible from the internet (or via VPN/tunnel)
4. **Kubeconfig File**: Your cluster's kubeconfig file

## 🔧 Step 1: Prepare Your Repository

### 1.1 Create `.streamlit/config.toml` (Optional)

```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

### 1.2 Update `.gitignore`

Ensure sensitive files are ignored:
```
.env
*.log
kubeconfig*.yaml
*.db
__pycache__/
```

## 🔐 Step 2: Configure Kubeconfig Access

### Option 1: Streamlit Secrets (Recommended)

1. **Go to Streamlit Cloud** → Your App → Settings → Secrets

2. **Add kubeconfig as base64**:
   ```toml
   KUBECONFIG_BASE64 = "base64_encoded_kubeconfig_content"
   ```
   
   To encode your kubeconfig:
   ```bash
   cat ~/.kube/config | base64
   ```

3. **Or add as file path** (if available):
   ```toml
   KUBECONFIG = "/path/to/kubeconfig"
   ```

### Option 2: Environment Variables

In Streamlit Cloud deployment settings:
- Set `KUBECONFIG_BASE64` with base64 encoded kubeconfig
- Or set `KUBECONFIG` with file path

### Option 3: File Upload in UI

Users can upload kubeconfig directly in the Streamlit UI:
1. Select "Upload kubeconfig file"
2. Upload the kubeconfig YAML file
3. File is stored temporarily for the session

## 🌐 Step 3: Make Cluster Accessible

### For Public Clusters (EKS, AKS, GKE)

Most cloud-managed Kubernetes clusters have public API endpoints:
- **AWS EKS**: API server is accessible via public endpoint
- **Azure AKS**: Can enable public API server
- **GCP GKE**: Public endpoint available

**Configuration**:
- Use your cloud provider's kubeconfig
- Ensure API server is publicly accessible
- Configure firewall rules if needed

### For Private Clusters

If your cluster is private, you need:

#### Option A: VPN/Tunnel
- Set up VPN connection from Streamlit Cloud
- Use tools like `kubectl port-forward` or `ngrok`
- Configure kubeconfig to use tunnel endpoint

#### Option B: Ingress with Public Endpoint
- Expose cluster API via Ingress
- Use public domain name
- Update kubeconfig server URL

#### Option C: Cloud Provider Proxy
- Use cloud provider's proxy service
- AWS: EKS API proxy
- Azure: AKS API proxy
- GCP: GKE API proxy

## 📝 Step 4: Deploy to Streamlit Cloud

### 4.1 Connect Repository

1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect your GitHub repository
4. Select branch: `main`
5. Main file path: `multi-agent-sre-bot/app.py`

### 4.2 Configure Secrets

Add to Streamlit Secrets:
```toml
# API Keys
NEBIUS_API_KEY = "your_nebius_api_key"
OPENAI_API_KEY = "your_openai_api_key"  # Optional

# Kubernetes Configuration
KUBECONFIG_BASE64 = "base64_encoded_kubeconfig"
# OR
KUBECONFIG = "/path/to/kubeconfig"  # If available

# Optional: Platform-specific
K8S_PLATFORM = "aws"  # or "azure", "gcp", "local"
```

### 4.3 Deploy

Click "Deploy" and wait for deployment to complete.

## 🎯 Step 5: Using the Deployed App

### 5.1 Access the App

1. Open your Streamlit Cloud app URL
2. You'll see the Multi-Agent SRE Bot UI

### 5.2 Configure API Keys

1. Enter **Nebius API Key** in sidebar
2. Enter **OpenAI API Key** (optional)
3. Click "Validate Keys"

### 5.3 Configure Kubernetes

**Option A: Using Secrets** (Already configured)
- Select "Use kubeconfig from environment"
- Kubeconfig is loaded from `KUBECONFIG_BASE64`

**Option B: Upload File**
- Select "Upload kubeconfig file"
- Upload your kubeconfig
- File is used for current session

### 5.4 Initialize Bot

1. Click "🚀 Initialize Multi-Agent System"
2. Bot connects to your cluster
3. All agents initialize
4. Chat interface becomes active

## 🔍 Troubleshooting

### Issue: Cannot Connect to Cluster

**Solutions**:
1. Verify kubeconfig is correct
2. Check cluster API server is accessible
3. Verify firewall rules allow Streamlit Cloud IPs
4. Test connection: `kubectl cluster-info --kubeconfig <your-kubeconfig>`

### Issue: Kubeconfig Not Found

**Solutions**:
1. Check Streamlit Secrets are set correctly
2. Verify base64 encoding is correct
3. Try uploading kubeconfig file directly
4. Check file path if using `KUBECONFIG` variable

### Issue: Cluster Not Accessible

**Solutions**:
1. For private clusters: Set up VPN/tunnel
2. Check network connectivity
3. Verify API server endpoint is correct
4. Check authentication credentials in kubeconfig

### Issue: Import Errors

**Solutions**:
1. Ensure all dependencies are in `requirements.txt`
2. Check Python version compatibility
3. Review deployment logs in Streamlit Cloud

## 📊 Best Practices

### Security
- ✅ Never commit kubeconfig to git
- ✅ Use Streamlit Secrets for sensitive data
- ✅ Rotate API keys regularly
- ✅ Use read-only service accounts when possible
- ✅ Enable RBAC in Kubernetes

### Performance
- ✅ Use connection pooling
- ✅ Cache cluster information
- ✅ Limit concurrent operations
- ✅ Monitor API rate limits

### Reliability
- ✅ Handle connection failures gracefully
- ✅ Implement retry logic
- ✅ Log all operations
- ✅ Monitor cluster connectivity

## 🎯 Example Streamlit Secrets

```toml
# .streamlit/secrets.toml (for local testing)
NEBIUS_API_KEY = "your_key_here"
OPENAI_API_KEY = "your_key_here"
KUBECONFIG_BASE64 = "base64_encoded_kubeconfig"
K8S_PLATFORM = "aws"
```

## 📝 Deployment Checklist

- [ ] Repository is on GitHub
- [ ] `.streamlit/config.toml` created (optional)
- [ ] `.gitignore` excludes sensitive files
- [ ] `requirements.txt` includes all dependencies
- [ ] Streamlit Secrets configured
- [ ] Kubeconfig encoded and added to secrets
- [ ] Cluster is accessible from internet
- [ ] API keys are set in secrets
- [ ] App deployed successfully
- [ ] Bot can connect to cluster
- [ ] All agents initialize correctly

## 🚀 Quick Start

1. **Encode kubeconfig**:
   ```bash
   cat ~/.kube/config | base64 > kubeconfig_base64.txt
   ```

2. **Add to Streamlit Secrets**:
   ```toml
   KUBECONFIG_BASE64 = "paste_base64_content_here"
   NEBIUS_API_KEY = "your_key"
   ```

3. **Deploy**:
   - Connect GitHub repo
   - Set main file: `multi-agent-sre-bot/app.py`
   - Deploy

4. **Use**:
   - Open app URL
   - Select "Use kubeconfig from environment"
   - Initialize bot
   - Start chatting!

## ✅ Success Indicators

- ✅ App loads without errors
- ✅ API keys validate successfully
- ✅ Kubeconfig loads from secrets
- ✅ Bot connects to cluster
- ✅ All agents initialize
- ✅ Chat interface works
- ✅ Can execute cluster operations

Your Multi-Agent SRE Bot is now deployed and ready to use! 🎉

