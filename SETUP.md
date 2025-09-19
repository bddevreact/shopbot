# MrZoidbergBot Setup Guide

## Quick Start

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your bot:**
   - Edit `config.env` with your actual bot token and crypto addresses
   - Replace the demo values with your real credentials

3. **Run the bot:**
   ```bash
   python bot.py
   ```

## Optional: Enable PGP Features

If you want to use PGP verification features:

1. **Install GPG for Windows:**
   - Download from: https://www.gpg4win.org/
   - Install with default settings

2. **Generate PGP keys:**
   ```bash
   gpg --gen-key
   ```

3. **Export your public key:**
   ```bash
   gpg --armor --export your-email@example.com
   ```

4. **Update config.env:**
   - Add your public key to `PGP_PUBLIC_KEY`
   - Add your passphrase to `PGP_PRIVATE_PASSPHRASE`

5. **Restart the bot**

## Features

- ✅ E-commerce product catalog
- ✅ Shopping cart functionality
- ✅ Cryptocurrency payments (BTC/XMR)
- ✅ QR code generation for payments
- ✅ Country selection (GER, AUS, USA)
- ✅ Order tracking
- ✅ PGP verification (optional)
- ✅ Secure configuration management

## Security Notes

- Never commit `config.env` to version control
- Use strong, unique passphrases for PGP keys
- Keep your bot token secure
- Use real cryptocurrency addresses for production

## Troubleshooting

**"GPG not available" error:**
- Install GPG for Windows from the link above
- Or ignore the warning - PGP features will be disabled

**"BOT_TOKEN not found" error:**
- Check that `config.env` exists and contains your bot token
- Make sure the file is in the same directory as `bot.py`
