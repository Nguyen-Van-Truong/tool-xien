const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

const { ProfileWorker, detectAllBrowsers, CONFIG, LOCAL_BROWSER_DIR } = require('./worker');

let mainWindow;
let worker;
let selectedBrowserId = null;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1300,
        height: 850,
        minWidth: 1000,
        minHeight: 650,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        title: 'GG Profile Saver',
        backgroundColor: '#0f0f1a'
    });
    mainWindow.loadFile('index.html');
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });

// ======================== IPC HANDLERS ========================

ipcMain.handle('detect-browsers', async () => detectAllBrowsers());

ipcMain.handle('download-browser', async () => {
    const { execFile } = require('child_process');
    const npxPath = process.platform === 'win32' ? 'npx.cmd' : 'npx';
    return new Promise((resolve) => {
        const child = execFile(npxPath, ['puppeteer', 'browsers', 'install', 'chrome'], {
            cwd: __dirname,
            env: { ...process.env, PUPPETEER_CACHE_DIR: LOCAL_BROWSER_DIR },
            timeout: 600000,
        }, (error, stdout, stderr) => {
            if (error) {
                resolve({ success: false, error: error.message });
            } else {
                resolve({ success: true, output: stdout });
            }
        });
    });
});

ipcMain.handle('set-browser', async (event, browserId) => {
    selectedBrowserId = browserId;
    return true;
});

// ---- Login All ----
ipcMain.handle('start-login', async (event, data) => {
    const accounts = data.accounts;
    const options = data.options || {};
    worker = new ProfileWorker(mainWindow, selectedBrowserId, options);
    await worker.startLoginAll(accounts);
    return true;
});

ipcMain.handle('stop-login', async () => {
    if (worker) worker.stop();
    return true;
});

ipcMain.handle('close-all-browsers', async () => {
    if (worker) return await worker.closeAllBrowsers();
    return 0;
});

// ---- Profiles ----
ipcMain.handle('get-profiles', async () => {
    const w = new ProfileWorker(null);
    return w.getProfiles();
});

ipcMain.handle('open-profile', async (event, email) => {
    if (!worker) worker = new ProfileWorker(mainWindow, selectedBrowserId);
    return await worker.openProfile(email);
});

ipcMain.handle('open-all-profiles', async () => {
    if (!worker) worker = new ProfileWorker(mainWindow, selectedBrowserId);
    return await worker.openAllProfiles();
});

ipcMain.handle('delete-profile', async (event, email) => {
    const w = new ProfileWorker(mainWindow);
    return w.deleteProfile(email);
});

ipcMain.handle('clean-profiles', async () => {
    const w = new ProfileWorker(mainWindow);
    return w.cleanProfiles();
});

// ---- Import ----
ipcMain.handle('import-accounts', async () => {
    const w = new ProfileWorker(mainWindow);
    return w.importAccounts();
});

// ---- Accounts file ----
ipcMain.handle('read-accounts', async () => {
    const w = new ProfileWorker(null);
    return w.readAccountsFile();
});

ipcMain.handle('save-accounts', async (event, content) => {
    const w = new ProfileWorker(null);
    w.saveAccountsFile(content);
    return true;
});

// ---- Backup / Restore ----
ipcMain.handle('backup', async () => {
    const w = new ProfileWorker(mainWindow);
    return w.backup();
});

ipcMain.handle('list-backups', async () => {
    const w = new ProfileWorker(null);
    return w.listBackups();
});

ipcMain.handle('restore', async (event, name) => {
    const w = new ProfileWorker(mainWindow);
    return w.restore(name);
});

// ---- Temp & Cache ----
function getFolderSize(folderPath) {
    let totalSize = 0;
    try {
        if (!fs.existsSync(folderPath)) return 0;
        const files = fs.readdirSync(folderPath);
        for (const file of files) {
            const filePath = path.join(folderPath, file);
            try {
                const stats = fs.statSync(filePath);
                if (stats.isDirectory()) totalSize += getFolderSize(filePath);
                else totalSize += stats.size;
            } catch (e) {}
        }
    } catch (e) {}
    return totalSize;
}

ipcMain.handle('get-profiles-size', async () => {
    const size = getFolderSize(CONFIG.PROFILES_DIR);
    return {
        sizeMB: Math.round(size / 1024 / 1024 * 100) / 100,
        sizeBytes: size
    };
});

ipcMain.handle('get-temp-size', async () => {
    const tempPath = path.join(process.env.LOCALAPPDATA || '', 'Temp');
    let totalSize = 0, folderCount = 0;
    try {
        const items = fs.readdirSync(tempPath);
        for (const item of items) {
            if (item.startsWith('puppeteer')) {
                folderCount++;
                const itemPath = path.join(tempPath, item);
                try {
                    const stats = fs.statSync(itemPath);
                    if (stats.isDirectory()) totalSize += getFolderSize(itemPath);
                    else totalSize += stats.size;
                } catch (e) {}
            }
        }
    } catch (e) {}
    return { sizeMB: Math.round(totalSize / 1024 / 1024 * 100) / 100, sizeBytes: totalSize, folderCount };
});

ipcMain.handle('clear-temp', async () => {
    const tempPath = path.join(process.env.LOCALAPPDATA || '', 'Temp');
    let deletedCount = 0;
    try {
        const items = fs.readdirSync(tempPath);
        for (const item of items) {
            if (item.startsWith('puppeteer')) {
                try {
                    fs.rmSync(path.join(tempPath, item), { recursive: true, force: true });
                    deletedCount++;
                } catch (e) {}
            }
        }
    } catch (e) {}
    return { deletedCount };
});
