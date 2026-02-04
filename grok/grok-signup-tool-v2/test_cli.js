/**
 * CLI Test Script
 * Run Grok signup without GUI for quick testing
 */

const { GrokWorker } = require('./grok_worker');
const { generateAccounts } = require('./generate_accounts');
const fs = require('fs');

// Console colors
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    red: '\x1b[31m',
    cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

/**
 * Mock main window for CLI mode
 */
class MockWindow {
    constructor() {
        this.webContents = {
            send: (channel, data) => {
                // Just log instead of sending to GUI
                if (channel === 'log') {
                    const typeColors = {
                        success: 'green',
                        error: 'red',
                        warning: 'yellow',
                        info: 'cyan'
                    };
                    log(data.message, typeColors[data.type] || 'reset');
                } else if (channel === 'progress') {
                    const percent = data.total > 0 ? Math.round((data.current / data.total) * 100) : 0;
                    log(`📊 Progress: ${data.current}/${data.total} (${percent}%) - ${data.text}`, 'cyan');
                } else if (channel === 'result') {
                    log(`📈 Stats: Success=${data.success}, Failed=${data.failed}`, 'bright');
                }
            }
        };
    }
}

/**
 * Main CLI test function
 */
async function runCLITest() {
    log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'bright');
    log('🤖 Grok Signup Tool V2 - CLI Test Mode', 'bright');
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', 'bright');

    // Parse command line args
    let args = process.argv.slice(2);
    let accounts = [];
    let maxConcurrent = 5; // Default

    // Extract --max or -m flag
    const maxIndex = args.findIndex(arg => arg === '--max' || arg === '-m');
    if (maxIndex >= 0 && args[maxIndex + 1]) {
        maxConcurrent = parseInt(args[maxIndex + 1]);
        args.splice(maxIndex, 2); // Remove from args
    }

    if (args.length === 0) {
        // Auto-generate 1 test account
        log('📝 No input provided - generating 1 test account...', 'yellow');
        accounts = generateAccounts(1);
    } else if (args[0] === '--generate' || args[0] === '-g') {
        // Generate N accounts
        const count = parseInt(args[1]) || 3;
        log(`📝 Generating ${count} test accounts...`, 'yellow');
        accounts = generateAccounts(count);
    } else if (args[0] === '--file' || args[0] === '-f') {
        // Read from file
        const filename = args[1] || 'accounts.txt';
        log(`📂 Reading accounts from ${filename}...`, 'yellow');
        const content = fs.readFileSync(filename, 'utf8');
        accounts = parseAccounts(content);
    } else {
        // Parse inline accounts
        accounts = parseAccounts(args.join(' '));
    }

    if (accounts.length === 0) {
        log('❌ No valid accounts to process!', 'red');
        printUsage();
        process.exit(1);
    }

    log(`\n🎯 Processing ${accounts.length} account(s) with max ${maxConcurrent} concurrent...\\n`, 'bright');

    // Display accounts
    accounts.forEach((acc, i) => {
        log(`[${i + 1}] ${acc.email} | ${acc.firstname} ${acc.lastname}`, 'cyan');
    });

    log('\n🚀 Starting signup process...\n', 'green');

    // Create mock window and worker
    const mockWindow = new MockWindow();
    const worker = new GrokWorker(mockWindow, null, {
        headless: false,
        maxConcurrent: maxConcurrent,
        keepBrowserOpen: true
    });

    // Clear old results
    if (fs.existsSync('success.txt')) fs.writeFileSync('success.txt', '');
    if (fs.existsSync('failed.txt')) fs.writeFileSync('failed.txt', '');

    // Run signup
    try {
        await worker.start(accounts);

        log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'bright');
        log('✅ Test completed!', 'green');
        log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', 'bright');

        // Show results
        displayResults();

    } catch (error) {
        log(`\n❌ Test failed: ${error.message}`, 'red');
        process.exit(1);
    }
}

/**
 * Parse accounts from text
 */
function parseAccounts(text) {
    const lines = text.trim().split('\n').filter(line => line.trim());
    return lines.map(line => {
        const parts = line.trim().split('|');
        if (parts.length >= 4) {
            return {
                email: parts[0].trim(),
                password: parts[1].trim(),
                firstname: parts[2].trim(),
                lastname: parts[3].trim()
            };
        }
        return null;
    }).filter(acc => acc);
}

/**
 * Display test results
 */
function displayResults() {
    const successFile = 'success.txt';
    const failedFile = 'failed.txt';

    if (fs.existsSync(successFile)) {
        const successContent = fs.readFileSync(successFile, 'utf8').trim();
        if (successContent) {
            const successCount = successContent.split('\n').length;
            log(`✅ SUCCESS (${successCount} accounts):`, 'green');
            successContent.split('\n').forEach(line => {
                log(`   ${line}`, 'green');
            });
        } else {
            log('✅ SUCCESS: 0 accounts', 'yellow');
        }
    }

    if (fs.existsSync(failedFile)) {
        const failedContent = fs.readFileSync(failedFile, 'utf8').trim();
        if (failedContent) {
            const failedCount = failedContent.split('\n').length;
            log(`\n❌ FAILED (${failedCount} accounts):`, 'red');
            failedContent.split('\n').forEach(line => {
                log(`   ${line}`, 'red');
            });
        }
    }

    log('\n📁 Results saved to success.txt and failed.txt', 'cyan');
}

/**
 * Print usage instructions
 */
function printUsage() {
    log('\n📖 Usage:', 'bright');
    log('  node test_cli.js                          # Auto-generate 1 account');
    log('  node test_cli.js -g 5                     # Generate 5 accounts');
    log('  node test_cli.js -g 10 -m 3               # Generate 10, max 3 concurrent');
    log('  node test_cli.js -f accounts.txt          # Read from file');
    log('  node test_cli.js -f accounts.txt -m 2     # From file, max 2 concurrent');
    log('  node test_cli.js "email|pass|first|last"  # Direct input\n');
}

// Run if called directly
if (require.main === module) {
    runCLITest().catch(error => {
        log(`\n❌ Fatal error: ${error.message}`, 'red');
        console.error(error);
        process.exit(1);
    });
}

module.exports = { runCLITest };
