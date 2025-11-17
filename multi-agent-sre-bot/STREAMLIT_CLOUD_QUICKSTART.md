# Streamlit Cloud Quick Start

## 🚀 Deploy in 5 Minutes

### Step 1: Prepare Kubeconfig

```bash
# Encode your kubeconfig
cat ~/.kube/config | base64 > kubeconfig_base64.txt
```

### Step 2: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect your GitHub repository
4. Main file: `multi-agent-sre-bot/app.py`
5. Branch: `main`

### Step 3: Add Secrets

In Streamlit Cloud → Settings → Secrets:

```toml
NEBIUS_API_KEY = "your_nebius_key"
OPENAI_API_KEY = "your_openai_key"  # Optional
KUBECONFIG_BASE64 = "paste_base64_from_step1"
```

### Step 4: Deploy

Click "Deploy" and wait for deployment.

### Step 5: Use the App

1. Open your app URL
2. Select "Use kubeconfig from environment"
3. Enter API keys (or they're already set from secrets)
4. Click "Initialize Multi-Agent System"
5. Start chatting!

## 📝 Alternative: Upload Kubeconfig

If you prefer not to use secrets:

1. In the UI, select "Upload kubeconfig file"
2. Upload your kubeconfig YAML
3. Initialize the bot

**Note**: Uploaded files are session-only and not persisted.

## ✅ That's It!

Your bot is now deployed and can access your Kubernetes cluster! 🎉

