# 🚀 Database Migration Guide for Render

## Current Status
✅ **Your service is live!** - https://procure-to-pay-server.onrender.com  
❌ **Database needs migration** - auth_user table missing

## Quick Fix Options

### Option 1: Automatic Redeploy (Recommended)
The build script now includes automatic migrations. Simply:

1. **Push these changes** to your repository
2. **Render will automatically redeploy** and run migrations
3. **Check the build logs** for migration output

### Option 2: Manual Migration via Render Shell
If you need to run migrations manually:

1. Go to your **Render dashboard**
2. Navigate to your **backend service**
3. Click **"Shell"** in the top menu
4. Run these commands:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

### Option 3: Use the Init Script
Upload and run the initialization script:
```bash
chmod +x init_render_db.sh
./init_render_db.sh
```

## What Will Happen
The migration will create these essential tables:
- ✅ `auth_user` (Django users)
- ✅ `auth_group` (User groups) 
- ✅ `auth_permission` (Permissions)
- ✅ All your custom procurement tables

## After Migration
Your API endpoints will work:
- 🏠 **Root**: https://procure-to-pay-server.onrender.com/ 
- 📖 **API Docs**: https://procure-to-pay-server.onrender.com/api/docs/
- 🔐 **Login**: https://procure-to-pay-server.onrender.com/api/auth/login/
- 🔧 **Admin**: https://procure-to-pay-server.onrender.com/admin/

## Next Steps
1. **Push changes** to trigger automatic redeploy with migrations
2. **Create admin user** for testing
3. **Test API endpoints** 
4. **Connect frontend** to the live backend

The 404 error on root is also fixed - you'll now see a JSON response with API information! 🎉