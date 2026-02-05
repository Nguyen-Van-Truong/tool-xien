/**
 * Grok Login Tool V2 - Main Process
 * Login + Auto Payment for SuperGrok Trial
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { GrokPaymentWorker } = require('./grok_payment_worker');

let mainWindow;
let grokWorker = null;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        },
        icon: path.join(__dirname, 'icon.png'),
        title: 'Grok Login + Payment Tool V2'
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

// IPC Handlers

// Start login + payment process
ipcMain.handle('start-process', async (event, accounts, cards, options) => {
    grokWorker = new GrokPaymentWorker(mainWindow, null, options);
    return await grokWorker.start(accounts, cards);
});

// Stop process
ipcMain.handle('stop-process', async () => {
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
        fs.writeFileSync(filePath, '');
    });

    return true;
});

// Get temp folder size
ipcMain.handle('get-temp-size', async () => {
    const tempPath = process.env.LOCALAPPDATA + '\\Temp';
    let totalSize = 0;
    let folderCount = 0;

    try {
        const items = fs.readdirSync(tempPath);
        for (const item of items) {
            if (item.startsWith('puppeteer')) {
                folderCount++;
                const itemPath = path.join(tempPath, item);
                try {
                    const stat = fs.statSync(itemPath);
                    if (stat.isDirectory()) {
                        totalSize += getFolderSize(itemPath);
                    }
                } catch (e) { }
            }
        }
    } catch (e) { }

    return {
        folderCount,
        sizeMB: Math.round(totalSize / 1024 / 1024 * 100) / 100
    };
});

function getFolderSize(folderPath) {
    let size = 0;
    try {
        const files = fs.readdirSync(folderPath);
        for (const file of files) {
            const filePath = path.join(folderPath, file);
            try {
                const stat = fs.statSync(filePath);
                if (stat.isDirectory()) {
                    size += getFolderSize(filePath);
                } else {
                    size += stat.size;
                }
            } catch (e) { }
        }
    } catch (e) { }
    return size;
}

// Delete browser data
ipcMain.handle('delete-browser-data', async () => {
    const tempPath = process.env.LOCALAPPDATA + '\\Temp';
    let deletedCount = 0;

    try {
        const items = fs.readdirSync(tempPath);
        for (const item of items) {
            if (item.startsWith('puppeteer')) {
                const itemPath = path.join(tempPath, item);
                try {
                    fs.rmSync(itemPath, { recursive: true, force: true });
                    deletedCount++;
                } catch (e) { }
            }
        }
    } catch (e) { }

    return { deletedCount };
});
