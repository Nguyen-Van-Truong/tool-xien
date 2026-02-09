/**
 * GitHub Signup Tool - Main Process
 * Electron app with IPC handlers
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { GitHubWorker } = require('./github_worker');

let mainWindow;
let githubWorker = null;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1300,
        height: 850,
        minWidth: 900,
        minHeight: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        },
        title: 'GitHub Signup Tool',
        backgroundColor: '#0d1117'
    });

    mainWindow.loadFile('index.html');
    // mainWindow.webContents.openDevTools();
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

// ========== IPC Handlers ==========

// Start signup process
ipcMain.handle('start-signup', async (event, accounts, options) => {
    githubWorker = new GitHubWorker(mainWindow, options);
    return await githubWorker.start(accounts);
});

// Stop signup process
ipcMain.handle('stop-signup', async () => {
    if (githubWorker) {
        await githubWorker.stop();
    }
    return true;
});

// Next account signal (user finished manual step)
ipcMain.handle('next-account', async (event, status) => {
    if (githubWorker) {
        githubWorker.resolveManualWait(status);
    }
    return true;
});

// Close all browsers
ipcMain.handle('close-all-browsers', async () => {
    if (githubWorker) {
        await githubWorker.closeAllBrowsers();
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
    ['success.txt', 'failed.txt'].forEach(filename => {
        const filePath = path.join(__dirname, filename);
        fs.writeFileSync(filePath, '');
    });
    return true;
});

// Helper: calculate folder size
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

// Get browser data size
ipcMain.handle('get-temp-size', async () => {
    const tempPath = path.join(process.env.LOCALAPPDATA || '', 'Temp');
    const puppeteerCache = path.join(process.env.USERPROFILE || '', '.cache', 'puppeteer');
    const chromiumData = path.join(process.env.LOCALAPPDATA || '', 'Chromium');

    let totalSize = 0;
    let folderCount = 0;

    // Temp folders
    try {
        const items = fs.readdirSync(tempPath);
        for (const item of items) {
            if (item.startsWith('puppeteer') || item.startsWith('chromium')) {
                folderCount++;
                const itemPath = path.join(tempPath, item);
                try {
                    totalSize += getFolderSize(itemPath);
                } catch (e) { }
            }
        }
    } catch (e) { }

    // Puppeteer cache
    if (fs.existsSync(puppeteerCache)) {
        folderCount++;
        totalSize += getFolderSize(puppeteerCache);
    }

    // Chromium data
    if (fs.existsSync(chromiumData)) {
        folderCount++;
        totalSize += getFolderSize(chromiumData);
    }

    return {
        folderCount,
        sizeMB: Math.round(totalSize / 1024 / 1024 * 100) / 100
    };
});

// Delete ALL browser data
ipcMain.handle('delete-browser-data', async () => {
    const tempPath = path.join(process.env.LOCALAPPDATA || '', 'Temp');
    const puppeteerCache = path.join(process.env.USERPROFILE || '', '.cache', 'puppeteer');
    const chromiumData = path.join(process.env.LOCALAPPDATA || '', 'Chromium');

    let deletedCount = 0;
    let freedSize = 0;

    // Puppeteer cache
    try {
        if (fs.existsSync(puppeteerCache)) {
            freedSize += getFolderSize(puppeteerCache);
            fs.rmSync(puppeteerCache, { recursive: true, force: true });
            deletedCount++;
        }
    } catch (e) { }

    // Chromium data
    try {
        if (fs.existsSync(chromiumData)) {
            freedSize += getFolderSize(chromiumData);
            fs.rmSync(chromiumData, { recursive: true, force: true });
            deletedCount++;
        }
    } catch (e) { }

    // Temp folders
    try {
        const items = fs.readdirSync(tempPath);
        for (const item of items) {
            if (item.startsWith('puppeteer') || item.startsWith('chromium')) {
                const itemPath = path.join(tempPath, item);
                try {
                    freedSize += getFolderSize(itemPath);
                    fs.rmSync(itemPath, { recursive: true, force: true });
                    deletedCount++;
                } catch (e) { }
            }
        }
    } catch (e) { }

    return {
        deletedCount,
        freedMB: Math.round(freedSize / 1024 / 1024 * 100) / 100
    };
});
