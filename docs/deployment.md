# Health Dashboard Deployment Guide

How to deploy your health analytics dashboard to a personal domain.

## 🎯 Deployment Options

### Option 1: Static Hosting (Easiest)

Best for: Simple deployment with auto-updates

**Recommended Services:**
- **Netlify** (free tier available)
- **Vercel** (free tier available)
- **GitHub Pages** (free)
- **Cloudflare Pages** (free)

**Steps:**

1. **Prepare repository:**
   ```bash
   cd ~/clawd/projects/health-analytics
   
   # Ensure dashboard data is in .gitignore (it is)
   # Only HTML, CSS, and update scripts go to repo
   ```

2. **Deploy to Netlify (example):**
   - Connect GitHub repo
   - Build command: `python3 scripts/generate_dashboard_data.py`
   - Publish directory: `dashboard`
   - Set up custom domain in Netlify settings

3. **Automated updates:**
   - Use GitHub Actions to regenerate data
   - Or: Webhook from Health Export app to trigger build

### Option 2: VPS/Self-Hosted

Best for: Full control, private hosting

**Requirements:**
- Linux VPS (Ubuntu/Debian recommended)
- Domain name with DNS configured
- Basic server admin knowledge

**Components:**
1. Web server (nginx or Apache)
2. SSL certificate (Let's Encrypt)
3. Automated data sync from Mac Mini

---

## 🚀 Detailed: Self-Hosted Setup

### Part 1: Server Setup

**1. Install nginx:**
```bash
# On Ubuntu/Debian
sudo apt update
sudo apt install nginx
```

**2. Configure nginx:**

Create `/etc/nginx/sites-available/health-dashboard`:

```nginx
server {
    listen 80;
    server_name health.your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name health.your-domain.com;
    
    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/health.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/health.your-domain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Dashboard location
    root /var/www/health-dashboard;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Optional: Basic auth for privacy
    auth_basic "Health Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    # Cache JSON data for 5 minutes
    location /data/ {
        expires 5m;
        add_header Cache-Control "public, must-revalidate";
    }
}
```

**3. Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/health-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**4. Install SSL certificate:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d health.your-domain.com
```

**5. Optional: Set up basic auth:**
```bash
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd your-username
```

### Part 2: Automated Data Sync

**On your Mac Mini (where health data lives):**

**1. Create sync script** `~/clawd/projects/health-analytics/deploy.sh`:

```bash
#!/bin/bash
# Sync dashboard to web server

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

**2. Make executable:**
```bash
chmod +x ~/clawd/projects/health-analytics/deploy.sh
```

**3. Set up SSH key auth (if not already):**
```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "health-dashboard-deploy"

# Copy to server
ssh-copy-id user@your-server.com
```

**4. Test deployment:**
```bash
cd ~/clawd/projects/health-analytics
./deploy.sh
```

**5. Automate with launchd (macOS):**

Create `~/Library/LaunchAgents/com.health.dashboard.update.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.health.dashboard.update</string>
    
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
    <string>/tmp/health-dashboard-update.log</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/health-dashboard-update-error.log</string>
</dict>
</plist>
```

**Load the launch agent:**
```bash
launchctl load ~/Library/LaunchAgents/com.health.dashboard.update.plist
```

Now your dashboard will auto-update daily at 8 AM!

---

## 📊 Option 3: GitHub Pages + Actions

**Pros:** Free, automated, version controlled  
**Cons:** Public repo (need private repo for privacy)

**1. Create GitHub Actions workflow** `.github/workflows/update-dashboard.yml`:

```yaml
name: Update Health Dashboard

on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 8 AM UTC
  workflow_dispatch:      # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      # Note: This requires your health data to be in the repo
      # or synced from somewhere secure
      - name: Generate dashboard data
        run: python3 scripts/generate_dashboard_data.py
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dashboard
          publish_branch: gh-pages
```

**2. Enable GitHub Pages:**
- Go to repo settings → Pages
- Source: Deploy from `gh-pages` branch
- Custom domain: `health.your-domain.com`

**3. Configure DNS:**
- Add CNAME record: `health` → `your-username.github.io`

---

## 🔒 Security Considerations

### Authentication Options

**1. Basic HTTP Auth** (nginx):
```nginx
auth_basic "Health Dashboard";
auth_basic_user_file /etc/nginx/.htpasswd;
```

**2. OAuth/SSO** (Cloudflare Access, Auth0):
- Recommended for shared hosting
- Provides login page
- Can integrate with Google/GitHub

**3. VPN Access**:
- Host behind VPN (Tailscale, WireGuard)
- Most secure option
- Dashboard only accessible via VPN

**4. IP Whitelist**:
```nginx
# Allow only your home/office IPs
allow 1.2.3.4;      # Your home IP
allow 5.6.7.8/24;   # Your office network
deny all;
```

### HTTPS/SSL

**Always use HTTPS!** Health data should never go over plain HTTP.

**Let's Encrypt** (free):
```bash
sudo certbot --nginx -d health.your-domain.com
```

**Cloudflare** (free):
- Enable "Full (strict)" SSL mode
- Automatic certificate management

---

## 📱 Mobile Access

The dashboard is fully responsive. For best mobile experience:

1. **Add to home screen** (iOS/Android):
   - Creates app-like icon
   - Fullscreen mode

2. **Progressive Web App (PWA)**:
   - Add manifest.json for app-like experience
   - Service worker for offline caching

---

## 🔄 Update Strategies

### Strategy 1: Push from Mac Mini
- Mac Mini generates data
- Pushes to web server via rsync/scp
- Best for: Simple setup, direct control

### Strategy 2: Pull from Server
- Server fetches data from Mac Mini
- Requires: Mac Mini accessible (VPN or port forwarding)
- Best for: Server-initiated updates

### Strategy 3: Cloud Sync
- Mac Mini → Cloud storage (Dropbox/S3)
- Server pulls from cloud
- Best for: Multi-device access, backups

---

## 🌐 DNS Setup

Point your domain to the hosting service:

**For VPS/Self-hosted:**
```
A record: health.your-domain.com → your-server-ip
```

**For Cloudflare Pages/Netlify:**
```
CNAME: health → your-project.pages.dev
```

**For GitHub Pages:**
```
CNAME: health → your-username.github.io
```

---

## ✅ Deployment Checklist

- [ ] Server/hosting configured
- [ ] SSL certificate installed
- [ ] Dashboard files uploaded
- [ ] Data generation tested
- [ ] Authentication configured (if desired)
- [ ] DNS records set
- [ ] Automated sync/deploy script working
- [ ] Cron/launchd scheduled for auto-updates
- [ ] Test access from phone/tablet
- [ ] Bookmark/add to home screen

---

## 🆘 Troubleshooting

**Dashboard shows "Failed to load":**
- Check file:// vs http:// - need web server for AJAX
- Verify JSON files exist in data/ directory
- Check browser console for errors

**Charts not rendering:**
- Ensure Chart.js CDN is accessible
- Check JSON data format
- Verify JavaScript console for errors

**Auto-update not working:**
- Check cron/launchd logs
- Verify script has execute permissions
- Test deploy script manually first

**SSL certificate errors:**
- Renew Let's Encrypt: `sudo certbot renew`
- Check certificate expiry: `sudo certbot certificates`

---

**Ready to deploy?** Choose your preferred method and follow the steps above!
