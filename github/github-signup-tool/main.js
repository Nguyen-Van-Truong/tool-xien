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
        backgroundColor: '#0d1117',
        icon: path.join(__dirname, 'icon.ico')
    });

    mainWindow.loadFile('index.html');
    // mainWindow.webContents.openDevTools();
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

// ========== IPC Handlers ==========

// Start signup process
ipcMain.handle('start-signup', async (event, accounts, options) => {
    githubWorker = new GitHubWorker(mainWindow, options);
    return await githubWorker.start(accounts);
});

// Stop signup - keeps browsers open!
ipcMain.handle('stop-signup', async () => {
    if (githubWorker) {
        await githubWorker.stop();
    }
    return true;
});

// Next account signal (user finished manual step)
ipcMain.handle('next-account', async (event, status, email) => {
    if (githubWorker) {
        githubWorker.resolveManualWait(email, status);
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

// Get browser count
ipcMain.handle('get-browser-count', async () => {
    if (githubWorker) {
        return githubWorker.browsers.length;
    }
    return 0;
});

// Read result files
ipcMain.handle('read-results', async () => {
    const readFile = (filename) => {
        const filePath = path.join(__dirname, filename);
        try {
            if (fs.existsSync(filePath)) return fs.readFileSync(filePath, 'utf8').trim();
        } catch (e) { }
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
        try { fs.writeFileSync(filePath, ''); } catch (e) { }
    });
    return true;
});

// ========== Browser Data Management ==========

function getFolderSize(folderPath) {
    let totalSize = 0;
    try {
        if (!fs.existsSync(folderPath)) return 0;
        const files = fs.readdirSync(folderPath);
        for (const file of files) {
            const fp = path.join(folderPath, file);
            try {
                const stats = fs.statSync(fp);
                totalSize += stats.isDirectory() ? getFolderSize(fp) : stats.size;
            } catch (e) { }
        }
    } catch (e) { }
    return totalSize;
}

ipcMain.handle('get-temp-size', async () => {
    const tempPath = path.join(process.env.LOCALAPPDATA || '', 'Temp');
    const puppeteerCache = path.join(process.env.USERPROFILE || '', '.cache', 'puppeteer');
    const chromiumData = path.join(process.env.LOCALAPPDATA || '', 'Chromium');

    let totalSize = 0;
    let folderCount = 0;

    try {
        const items = fs.readdirSync(tempPath);
        for (const item of items) {
            if (item.startsWith('puppeteer') || item.startsWith('chromium')) {
                folderCount++;
                try { totalSize += getFolderSize(path.join(tempPath, item)); } catch (e) { }
            }
        }
    } catch (e) { }

    if (fs.existsSync(puppeteerCache)) { folderCount++; totalSize += getFolderSize(puppeteerCache); }
    if (fs.existsSync(chromiumData)) { folderCount++; totalSize += getFolderSize(chromiumData); }

    return { folderCount, sizeMB: Math.round(totalSize / 1024 / 1024 * 100) / 100 };
});

ipcMain.handle('delete-browser-data', async () => {
    const tempPath = path.join(process.env.LOCALAPPDATA || '', 'Temp');
    const puppeteerCache = path.join(process.env.USERPROFILE || '', '.cache', 'puppeteer');
    const chromiumData = path.join(process.env.LOCALAPPDATA || '', 'Chromium');

    let deletedCount = 0;
    let freedSize = 0;

    const remove = (p) => {
        try {
            if (fs.existsSync(p)) {
                freedSize += getFolderSize(p);
                fs.rmSync(p, { recursive: true, force: true });
                deletedCount++;
            }
        } catch (e) { }
    };

    remove(puppeteerCache);
    remove(chromiumData);

    try {
        const items = fs.readdirSync(tempPath);
        for (const item of items) {
            if (item.startsWith('puppeteer') || item.startsWith('chromium')) {
                remove(path.join(tempPath, item));
            }
        }
    } catch (e) { }

    return { deletedCount, freedMB: Math.round(freedSize / 1024 / 1024 * 100) / 100 };
});
