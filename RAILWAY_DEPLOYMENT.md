# Railway Deployment Guide for MrZoidbergBot

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Push your bot code to GitHub
3. **Environment Variables**: Prepare your configuration

## Deployment Steps

### 1. Connect to Railway

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your MrZoidbergBot repository

### 2. Configure Environment Variables

In Railway dashboard, go to your project → Variables tab and add:

**Required Variables:**
```
BOT_TOKEN=your_telegram_bot_token
ADMIN_USER_ID=your_telegram_user_id
BTC_ADDRESS=your_bitcoin_address
XMR_ADDRESS=your_monero_address
```

**Optional Variables:**
```
PGP_PUBLIC_KEY=your_pgp_public_key
PGP_PRIVATE_PASSPHRASE=your_pgp_passphrase
LOG_LEVEL=INFO
ENABLE_LOGGING=true
ENABLE_BACKUPS=true
SHOP_NAME=MrZoidbergBot Shop
CURRENCY=EUR
DEFAULT_COUNTRY=GER
MAINTENANCE_MODE=false
```

### 3. Deploy

1. Railway will automatically detect the Python project
2. It will install dependencies from `requirements.txt`
3. The bot will start using the `Procfile` configuration

### 4. Monitor Deployment

- Check the "Deployments" tab for build logs
- Monitor the "Logs" tab for runtime logs
- The bot should start automatically after successful deployment

## Important Notes

### File Storage
- Railway provides ephemeral storage
- Data files (JSON configs) will be recreated on restart
- Consider using Railway's persistent volumes for production

### Environment Variables
- Never commit `config.env` with real tokens to Git
- Use Railway's environment variables instead
- The bot will automatically create default config files if they don't exist

### GPG Support
- GPG functionality may be limited on Railway
- The bot will gracefully disable PGP features if GPG is not available

### Monitoring
- Railway provides built-in monitoring and logging
- Set up alerts for deployment failures
- Monitor resource usage in the Railway dashboard

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Python version compatibility
   - Verify all dependencies in requirements.txt
   - Check build logs for specific errors

2. **Runtime Errors**
   - Verify all required environment variables are set
   - Check runtime logs for error messages
   - Ensure bot token is valid

3. **File Permission Issues**
   - Railway handles file permissions automatically
   - If issues persist, check file paths in code

### Support
- Check Railway documentation: [docs.railway.app](https://docs.railway.app)
- Railway Discord community for support
- Check bot logs for specific error messages

## Security Considerations

1. **Environment Variables**: Keep sensitive data in Railway's environment variables
2. **Bot Token**: Never expose in code or logs
3. **Crypto Addresses**: Verify addresses before deployment
4. **Admin Access**: Ensure only authorized users have admin access

## Post-Deployment

1. Test bot functionality
2. Verify admin commands work
3. Check cryptocurrency address generation
4. Test user registration and ordering flow
5. Monitor logs for any errors
