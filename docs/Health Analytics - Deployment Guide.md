---
created: 2026-01-26 21:00:00
updated: 2026-01-26 21:00:00
type: guide
tags: [p/health-analytics, tech/python, dev, deployment, devops, nginx, guide]
---

# Health Analytics - Deployment Guide

> Step-by-step guide for deploying the health analytics dashboard to your personal domain

## 🎯 Deployment Overview

The dashboard is a **static web application** - just HTML, CSS, JavaScript, and JSON data files. This makes it incredibly flexible to deploy anywhere.

### What You're Deploying

```
dashboard/
├── index.html          # Single HTML file (16 KB)
├── data/               # JSON data directory
│   ├── daily_trends.json
│   ├── weekly_comparison.json
│   ├── goals_progress.json
│   ├── summary_stats.json
│   └── metadata.json
└── .gitignore         # Protects JSON from commits
```

**Total size:** < 20 KB (excluding JSON data ~5 KB)

## 🌐 Option 1: Self-Hosted VPS (Recommended)

**Best for:** Full control, privacy, custom domain

### Prerequisites

- VPS running Ubuntu/Debian (DigitalOcean, Linode, etc.)
- Domain name with DNS access
- SSH access to server
- Basic Linux knowledge

### Step 1: Server Setup

**1.1 Install nginx**

```bash
# On Ubuntu/Debian
sudo apt update
sudo apt install nginx
```

**1.2 Create web directory**

```bash
sudo mkdir -p /var/www/health-dashboard
sudo chown -R $USER:$USER /var/www/health-dashboard
```

### Step 2: Configure nginx

**2.1 Create nginx config** (`/etc/nginx/sites-available/health-dashboard`):

```nginx
server {
    listen 80;
    server_name health.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name health.yourdomain.com;
    
    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/health.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/health.yourdomain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Dashboard root
    root /var/www/health-dashboard;
    index index.html;
    
    # Serve files
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Cache JSON data for 5 minutes
    location /data/ {
        expires 5m;
        add_header Cache-Control "public, must-revalidate";
    }
    
    # Optional: Basic authentication for privacy
    auth_basic "Health Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd;
}
```

**2.2 Enable the site**

```bash
sudo ln -s /etc/nginx/sites-available/health-dashboard /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

### Step 3: Install SSL Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d health.yourdomain.com

# Auto-renewal (should be automatic)
sudo certbot renew --dry-run
```

### Step 4: Set Up Basic Authentication (Optional)

```bash
# Install apache2-utils
sudo apt install apache2-utils

# Create password file
sudo htpasswd -c /etc/nginx/.htpasswd your-username
# Enter password when prompted
```

### Step 5: Configure DNS

**Add A record:**
```
Type: A
Name: health
Value: your-server-ip
TTL: 3600
```

Wait 5-60 minutes for DNS propagation.

### Step 6: Automated Sync from Mac Mini

**6.1 Set up SSH key auth**

On Mac Mini:
```bash
# Generate key if needed
ssh-keygen -t ed25519 -C "health-dashboard"

# Copy to server
ssh-copy-id user@your-server-ip
```

**6.2 Create deploy script** (`~/clawd/projects/health-analytics/deploy.sh`):

```bash
#!/bin/bash
# Deploy Health Dashboard to VPS

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER="user@your-server.com"
REMOTE_PATH="/var/www/health-dashboard"

echo "🔄 Generating fresh dashboard data..."
cd "$SCRIPT_DIR"
python3 scripts/generate_dashboard_data.py

if [ $? -ne 0 ]; then
    echo "❌ Data generation failed"
    exit 1
fi

echo "📤 Syncing to web server..."
rsync -avz --delete \
    --exclude='.git' \
    --exclude='*.md' \
    --exclude='scripts' \
    --exclude='README.md' \
    "$SCRIPT_DIR/dashboard/" \
    "$SERVER:$REMOTE_PATH/"

if [ $? -eq 0 ]; then
    echo "✅ Dashboard deployed successfully!"
    echo "🌐 https://health.your-domain.com"
else
    echo "❌ Deployment failed"
    exit 1
fi
```

```bash
chmod +x deploy.sh
```

**6.3 Test deployment**

```bash
./deploy.sh
```

### Step 7: Automate Daily Updates

**Create launchd plist** (`~/Library/LaunchAgents/com.health.dashboard.deploy.plist`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.health.dashboard.deploy</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/nick/clawd/projects/health-analytics/deploy.sh</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/tmp/health-dashboard-deploy.log</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/health-dashboard-deploy-error.log</string>
</dict>
</plist>
```

**Load it:**
```bash
launchctl load ~/Library/LaunchAgents/com.health.dashboard.deploy.plist

# Check logs
tail -f /tmp/health-dashboard-deploy.log
```

Dashboard will now update daily at 8 AM automatically! 🎉

## 🚀 Option 2: Netlify (Easiest)

**Best for:** Quick deployment, no server management

### Step 1: Push to GitHub

```bash
cd ~/clawd/projects/health-analytics
git remote add origin https://github.com/yourusername/health-analytics.git
git push -u origin main
```

### Step 2: Connect to Netlify

1. Go to [netlify.com](https://netlify.com)
2. Click "Add new site" → "Import an existing project"
3. Choose GitHub and select your repo
4. **Build settings:**
   - Build command: `python3 scripts/generate_dashboard_data.py`
   - Publish directory: `dashboard`
5. Deploy!

### Step 3: Custom Domain

1. In Netlify: Site settings → Domain management
2. Add custom domain: `health.yourdomain.com`
3. Configure DNS as instructed
4. SSL is automatic!

### Step 4: Automated Updates

**Option A: GitHub Actions** (`.github/workflows/update-dashboard.yml`):

```yaml
name: Update Dashboard

on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 8 AM UTC
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Generate dashboard data
        run: python3 scripts/generate_dashboard_data.py
      
      - name: Commit and push
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          git add dashboard/data/
          git commit -m "Update dashboard data" || exit 0
          git push
```

**Option B: Netlify Build Hooks**

Trigger deployment from Mac Mini:
```bash
# Add to your deploy script
curl -X POST -d {} https://api.netlify.com/build_hooks/YOUR_HOOK_ID
```

## 📊 Option 3: GitHub Pages

**Best for:** Free, simple, version controlled

### Step 1: Push to GitHub

```bash
cd ~/clawd/projects/health-analytics
git remote add origin https://github.com/yourusername/health-analytics.git
git push -u origin main
```

### Step 2: Enable GitHub Pages

1. Go to repo settings → Pages
2. Source: Deploy from branch `gh-pages`
3. Save

### Step 3: Deploy Script

Add to `deploy.sh`:

```bash
# Generate data
python3 scripts/generate_dashboard_data.py

# Deploy to gh-pages
git checkout -b gh-pages || git checkout gh-pages
git add dashboard/
git commit -m "Update dashboard"
git push origin gh-pages
git checkout main
```

### Step 4: Custom Domain

1. Create file `dashboard/CNAME` with: `health.yourdomain.com`
2. Add DNS CNAME record: `health` → `yourusername.github.io`
3. Enable HTTPS in GitHub Pages settings

## 🔐 Security Best Practices

### Authentication Options

**1. Basic HTTP Auth** (nginx):
```nginx
auth_basic "Health Dashboard";
auth_basic_user_file /etc/nginx/.htpasswd;
```

**2. VPN Access** (Tailscale/WireGuard):
- Most secure option
- Dashboard only accessible via VPN
- No public exposure

**3. IP Whitelist** (nginx):
```nginx
# Allow only your IPs
allow 1.2.3.4;        # Home IP
allow 5.6.7.8/24;     # Office network
deny all;
```

**4. OAuth/SSO** (Cloudflare Access, Auth0):
- Best for sharing with others
- Proper login page
- Can integrate with Google/GitHub

### HTTPS Requirements

**Always use HTTPS!** Health data should never go over plain HTTP.

**Certificate options:**
- Let's Encrypt (free, automated)
- Cloudflare (free, DNS-based)
- ZeroSSL (free alternative)

## 📱 Mobile Optimization

Dashboard is already responsive, but for best mobile experience:

**Add to home screen:**
1. Open in Safari/Chrome
2. Share → "Add to Home Screen"
3. Creates app-like icon

**Future: Progressive Web App**

Add `manifest.json` for full PWA:

```json
{
  "name": "Health Analytics",
  "short_name": "Health",
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#007AFF",
  "background_color": "#0f0f0f",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
```

## 🔧 Troubleshooting

### Dashboard shows "Failed to load"

**Issue:** JSON files not accessible

**Solutions:**
- Check files exist in `data/` directory
- Verify web server is serving the directory
- Check browser console for errors
- Ensure CORS is not blocking (if serving from different domain)

### Charts not rendering

**Issue:** Chart.js not loading

**Solutions:**
- Check internet connection (CDN dependency)
- Try self-hosting Chart.js
- Check browser console for JavaScript errors

### SSL certificate errors

**Issue:** Certificate expired or invalid

**Solutions:**
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test auto-renewal
sudo certbot renew --dry-run
```

### Automated deployment not working

**Issue:** Launchd job not running

**Solutions:**
```bash
# Check if loaded
launchctl list | grep health

# View logs
cat /tmp/health-dashboard-deploy.log
cat /tmp/health-dashboard-deploy-error.log

# Reload
launchctl unload ~/Library/LaunchAgents/com.health.dashboard.deploy.plist
launchctl load ~/Library/LaunchAgents/com.health.dashboard.deploy.plist
```

## ✅ Deployment Checklist

- [ ] Server/hosting configured
- [ ] SSL certificate installed and working
- [ ] Dashboard files uploaded
- [ ] DNS records set correctly
- [ ] Authentication configured (if desired)
- [ ] Test access from phone/tablet
- [ ] Automated deployment script working
- [ ] Scheduled updates configured (launchd/cron)
- [ ] Monitoring set up (uptime checks)
- [ ] Backup strategy in place

## 🔗 Related Documentation

- [[Health Analytics|Main Project]]
- [[Health Analytics - Technical Details|Technical Details]]
- [[Health Analytics - Analysis Scripts|Analysis Scripts]]

## 📚 External Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [nginx Configuration Guide](https://nginx.org/en/docs/)
- [Netlify Documentation](https://docs.netlify.com/)
- [GitHub Pages Guide](https://pages.github.com/)
- [Tailscale Setup](https://tailscale.com/kb/start)

---

**Need help deploying?** The deploy script handles most of the complexity. Start with the self-hosted VPS option for full control and privacy.
