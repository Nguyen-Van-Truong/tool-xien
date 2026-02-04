/**
 * Electron Main Process
 * Handles app initialization and IPC communication
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
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

    // Open DevTools in development
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

// Start signup process
ipcMain.handle('start-signup', async (event, accounts, options) => {
    grokWorker = new GrokWorker(mainWindow, null, options);
    return await grokWorker.start(accounts);
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

// Get Puppeteer temp folder size
ipcMain.handle('get-temp-size', async () => {
    const tempPath = path.join(process.env.LOCALAPPDATA || '', 'Temp');
    let totalSize = 0;
    let folderCount = 0;

    try {
        const items = fs.readdirSync(tempPath);
        for (const item of items) {
            if (item.startsWith('puppeteer')) {
                folderCount++;
                const itemPath = path.join(tempPath, item);
                try {
                    const stats = fs.statSync(itemPath);
                    if (stats.isDirectory()) {
                        // Calculate folder size recursively
                        const getFolderSize = (dirPath) => {
                            let size = 0;
                            try {
                                const files = fs.readdirSync(dirPath);
                                for (const file of files) {
                                    const filePath = path.join(dirPath, file);
                                    const stat = fs.statSync(filePath);
                                    if (stat.isDirectory()) {
                                        size += getFolderSize(filePath);
                                    } else {
                                        size += stat.size;
                                    }
                                }
                            } catch (e) { }
                            return size;
                        };
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

    return {
        sizeBytes: totalSize,
        sizeMB: Math.round(totalSize / 1024 / 1024 * 100) / 100,
        folderCount: folderCount
    };
});

// Delete Puppeteer browser data
ipcMain.handle('delete-browser-data', async () => {
    const tempPath = path.join(process.env.LOCALAPPDATA || '', 'Temp');
    let deletedCount = 0;

    try {
        const items = fs.readdirSync(tempPath);
        for (const item of items) {
            if (item.startsWith('puppeteer')) {
                const itemPath = path.join(tempPath, item);
                try {
                    const stats = fs.statSync(itemPath);
                    if (stats.isDirectory()) {
                        fs.rmSync(itemPath, { recursive: true, force: true });
                    } else {
                        fs.unlinkSync(itemPath);
                    }
                    deletedCount++;
                } catch (e) {
                    console.log('Cannot delete:', item, e.message);
                }
            }
        }
    } catch (e) {
        console.log('Error clearing temp:', e.message);
    }

    return { deletedCount };
});
