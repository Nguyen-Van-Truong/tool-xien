# CLI Test Mode & Account Generator - Quick Guide

## 🎯 Features Added

### 1. Auto-generate Test Accounts
```bash
# Generate 5 accounts (default)
node generate_accounts.js

# Generate custom number
node generate_accounts.js 10

# Or use npm script
npm run generate 5
```

### 2. CLI Test Mode (No GUI)

**Quick Start:**
```bash
# Auto-generate 1 account and test
npm run test:auto

# Auto-generate 3 accounts and test
npm run test:batch

# Manual test
npm test
```

**Advanced Usage:**
```bash
# Auto-generate 1 account
node test_cli.js

# Generate 5 accounts
node test_cli.js -g 5

# Read from file
node test_cli.js -f accounts.txt

# Direct input
node test_cli.js "email|pass|first|last"
```

## 📊 Output

CLI mode shows:
- ✅ Real-time colored logs
- 📊 Progress updates
- 📈 Final statistics
- 📁 Results in success.txt & failed.txt

## 🔧 Benefits

1. **Fast Testing** - No need to open GUI
2. **Auto Data** - Random realistic accounts
3. **Batch Ready** - Test multiple accounts easily
4. **CI/CD Ready** - Scriptable for automation

## ⚠️ Current Issue

**Email API (tinyhost.shop) may have connectivity issues.**

If test fails with DNS error, alternatives:
1. Use different temp email service
2. Use real emails for testing
3. Wait and retry (API might be down)

## 📝 Example Session

```bash
$ npm run test:auto

🤖 Grok Signup Tool V2 - CLI Test Mode
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Generating 1 test account...
🎯 Processing 1 account(s)...

[1] john.smith.abc123@gmail.com | John Smith

🚀 Starting signup process...
📧 Step 1/10: Generating temp email...
✅ Temp email: grok_123456@domain.com
🌐 Step 2/10: Launching browser...
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Test completed!

✅ SUCCESS (1 accounts):
   john.smith.abc123@gmail.com|Pass123!|...
```

## 🚀 Next Steps

1. **Fix email API** - Find stable alternative
2. **Add more generators** - Different name styles
3. **Add proxy support** - For batch signups
4. **Add retry logic** - Auto-retry on failures
