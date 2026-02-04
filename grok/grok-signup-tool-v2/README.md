# Grok Signup Tool V2

Automated Grok account signup tool with Electron GUI and Puppeteer automation.

## Features

- 🤖 **Automated Signup** - Complete Grok account creation flow
- 📧 **Temp Email** - Auto-generate temporary emails via tinyhost.shop
- 🔐 **OTP Handling** - Automatic verification code retrieval
- 🎨 **Dark Theme GUI** - Beautiful Electron interface
- 📊 **Batch Processing** - Create multiple accounts efficiently
- ✅ **Success Verification** - API-based account validation

## Installation

```bash
cd e:\tool xien\grok\grok-signup-tool-v2
npm install
```

## Usage

### Start GUI

```bash
npm start
```

### Input Format

```
email|password|firstname|lastname

Example:
myaccount@gmail.com|Pass123!|John|Doe
another@domain.com|SecurePass456|Jane|Smith
```

### Steps

1. Launch app with `npm start`
2. Select browser from dropdown
3. Paste accounts in input panel (format: email|pass|first|last)
4. Click **▶ RUN**
5. Watch progress in log panel
6. Results saved to `success.txt` and `failed.txt`

## How It Works

1. **Generate Temp Email** - Creates temporary email via API
2. **Navigate to Signup** - Opens accounts.x.ai/sign-up
3. **Fill Email** - Enters temp email
4. **Get OTP** - Retrieves verification code from inbox
5. **Submit OTP** - Enters code to verify email
6. **Complete Signup** - Fills firstname, lastname, password
7. **Verify Success** - Checks account via Grok API

## Result Files

- **success.txt** - Successfully created accounts
  - Format: `email|password|temp_email|otp|timestamp`
- **failed.txt** - Failed signups with error reasons
  - Format: `email|error|timestamp`

## Troubleshooting

### "No temp email generated"
- Check tinyhost.shop API status
- Verify network connection

### "OTP not received"
- Wait longer (increase timeout)
- Check spam/junk folder logic

### "Cloudflare challenge"
- Use visible browser (not headless)
- Puppeteer usually auto-solves

### "Success verification fails"
- Check if account actually created
- Verify API endpoint hasn't changed

## Tech Stack

- **Electron** - Desktop app framework
- **Puppeteer** - Browser automation
- **Axios** - HTTP requests
- **Node.js** - Runtime

## Development

```bash
# Run in dev mode
npm start

# Build executable
npm run build

# Test single account
npm test
```

## Credits

Based on gg login flow_v3 architecture.

## License

MIT
