/**
 * Electron Main Process
 * Handles app initialization and IPC communication
 */

const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

// Global error handler
process.on('uncaughtException', (err) => {
    const logPath = path.join(path.dirname(process.execPath), 'crash.log');
    fs.writeFileSync(logPath, `[${new Date().toISOString()}] ${err.message}\n${err.stack}\n`);
    if (app.isReady()) dialog.showErrorBox('Error', err.message);
    process.exit(1);
});

const { GrokWorker } = require('./grok_worker');

let mainWindow;
let grokWorker;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 900,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        title: 'Grok Signup Tool V2',
        backgroundColor: '#1a1a2e'
    });

    mainWindow.loadFile('index.html');
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// IPC Handlers

// Start signup process
ipcMain.handle('start-signup', async (event, config, options) => {
    grokWorker = new GrokWorker(mainWindow, null, options);
    return await grokWorker.start(config);
});

// Stop signup process
ipcMain.handle('stop-signup', async () => {
    if (grokWorker) {
        await grokWorker.stop();
    }
    return true;
});

// Close all browsers
ipcMain.handle('close-all-browsers', async () => {
    if (grokWorker) {
        await grokWorker.closeAllBrowsers();
    }
    return true;
});

// Read result files
ipcMain.handle('read-results', async () => {
    const readFile = (filename) => {
        const filePath = path.join(__dirname, filename);
        if (fs.existsSync(filePath)) {
            return fs.readFileSync(filePath, 'utf8').trim();
        }
        return '';
    };

    return {
        success: readFile('success.txt'),
        failed: readFile('failed.txt')
    };
});

// Clear result files
ipcMain.handle('clear-results', async () => {
    const files = ['success.txt', 'failed.txt'];

    files.forEach(filename => {
        const filePath = path.join(__dirname, filename);
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
        }
        // Create empty file
        fs.writeFileSync(filePath, '');
    });

    return true;
});

// Generate accounts handler
ipcMain.handle('generate-accounts', async (event, count) => {
    const { generateAccounts, formatForInput } = require('./generate_accounts');
    const accounts = generateAccounts(count);
    return formatForInput(accounts);
});

// Get ALL browser data size (Temp + Puppeteer cache + Chromium data)
ipcMain.handle('get-temp-size', async () => {
    const tempPath = path.join(process.env.LOCALAPPDATA || '', 'Temp');
    const puppeteerCache = path.join(process.env.USERPROFILE || '', '.cache', 'puppeteer');
    const chromiumData = path.join(process.env.LOCALAPPDATA || '', 'Chromium');

    let totalSize = 0;
    let folderCount = 0;

    // 1. Count puppeteer* and chromium* temp folders
    try {
        const items = fs.readdirSync(tempPath);
        for (const item of items) {
            if (item.startsWith('puppeteer') || item.startsWith('chromium')) {
                folderCount++;
                const itemPath = path.join(tempPath, item);
                try {
                    const stats = fs.statSync(itemPath);
                    if (stats.isDirectory()) {
                        totalSize += getFolderSize(itemPath);
                    } else {
                        totalSize += stats.size;
                    }
                } catch (e) { }
            }
        }
    } catch (e) {
        console.log('Error getting temp size:', e.message);
    }

    // 2. Count puppeteer cache
    if (fs.existsSync(puppeteerCache)) {
        folderCount++;
        totalSize += getFolderSize(puppeteerCache);
    }

    // 3. Count Chromium data
    if (fs.existsSync(chromiumData)) {
        folderCount++;
        totalSize += getFolderSize(chromiumData);
    }

    return {
        sizeBytes: totalSize,
        sizeMB: Math.round(totalSize / 1024 / 1024 * 100) / 100,
        folderCount: folderCount
    };
});

// Helper function to calculate folder size
function getFolderSize(folderPath) {
    let totalSize = 0;
    try {
        if (!fs.existsSync(folderPath)) return 0;
        const files = fs.readdirSync(folderPath);
        for (const file of files) {
            const filePath = path.join(folderPath, file);
            try {
                const stats = fs.statSync(filePath);
                if (stats.isDirectory()) {
                    totalSize += getFolderSize(filePath);
                } else {
                    totalSize += stats.size;
                }
            } catch (e) { }
        }
    } catch (e) { }
    return totalSize;
}

// Delete ALL browser data (Puppeteer cache + Chromium data + Temp folders)
ipcMain.handle('delete-browser-data', async () => {
    const tempPath = path.join(process.env.LOCALAPPDATA || '', 'Temp');
    const puppeteerCache = path.join(process.env.USERPROFILE || '', '.cache', 'puppeteer');
    const chromiumData = path.join(process.env.LOCALAPPDATA || '', 'Chromium');

    let deletedCount = 0;
    let freedSize = 0;

    // 1. Delete puppeteer cache (~/.cache/puppeteer)
    try {
        if (fs.existsSync(puppeteerCache)) {
            freedSize += getFolderSize(puppeteerCache);
            fs.rmSync(puppeteerCache, { recursive: true, force: true });
            deletedCount++;
            console.log('✅ Deleted puppeteer cache');
        }
    } catch (e) {
        console.log('Cannot delete puppeteer cache:', e.message);
    }

    // 2. Delete Chromium user data (LocalAppData\Chromium)
    try {
        if (fs.existsSync(chromiumData)) {
            freedSize += getFolderSize(chromiumData);
            fs.rmSync(chromiumData, { recursive: true, force: true });
            deletedCount++;
            console.log('✅ Deleted Chromium data');
        }
    } catch (e) {
        console.log('Cannot delete Chromium data:', e.message);
    }

    // 3. Delete puppeteer* and chromium* temp folders
    try {
        const items = fs.readdirSync(tempPath);
        for (const item of items) {
            if (item.startsWith('puppeteer') || item.startsWith('chromium')) {
                const itemPath = path.join(tempPath, item);
                try {
                    freedSize += getFolderSize(itemPath);
                    fs.rmSync(itemPath, { recursive: true, force: true });
                    deletedCount++;
                } catch (e) {
                    console.log('Cannot delete:', item, e.message);
                }
            }
        }
    } catch (e) {
        console.log('Error clearing temp:', e.message);
    }

    const freedMB = Math.round(freedSize / 1024 / 1024 * 100) / 100;
    console.log(`🗑️ Cleared ${deletedCount} items, freed ${freedMB} MB`);
    return { deletedCount, freedMB };
});
