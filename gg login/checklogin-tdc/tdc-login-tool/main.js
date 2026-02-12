const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

const { LoginWorker, detectAllBrowsers } = require('./worker');

let mainWindow;
let loginWorker;
let selectedBrowserId = null;

function getBasePath() {
    if (process.env.PORTABLE_EXECUTABLE_DIR) {
        return process.env.PORTABLE_EXECUTABLE_DIR;
    } else if (process.resourcesPath && !process.resourcesPath.includes('node_modules')) {
        return path.dirname(process.resourcesPath);
    }
    return __dirname;
}

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
        title: 'TDC Login Checker',
        backgroundColor: '#1a1a2e'
    });
    mainWindow.loadFile('index.html');
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });

// IPC Handlers
ipcMain.handle('detect-browsers', async () => detectAllBrowsers());

ipcMain.handle('set-browser', async (event, browserId) => {
    selectedBrowserId = browserId;
    return true;
});

ipcMain.handle('start-login', async (event, data) => {
    const accounts = data.accounts;
    const options = data.options || {};
    loginWorker = new LoginWorker(mainWindow, selectedBrowserId, options);
    return await loginWorker.start(accounts);
});

ipcMain.handle('stop-login', async () => {
    if (loginWorker) await loginWorker.stop();
    return true;
});

ipcMain.handle('close-all-browsers', async () => {
    if (loginWorker) await loginWorker.closeAllBrowsers();
    return true;
});

ipcMain.handle('read-results', async () => {
    const basePath = getBasePath();
    const readFile = (filename) => {
        const filePath = path.join(basePath, filename);
        return fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf8').trim() : '';
    };
    return {
        passed: readFile('passed.txt'),
        hasPhone: readFile('has_phone.txt'),
        needPhone: readFile('need_phone.txt'),
        loginFailed: readFile('login_failed.txt')
    };
});

ipcMain.handle('clear-results', async () => {
    const basePath = getBasePath();
    ['passed.txt', 'has_phone.txt', 'need_phone.txt', 'login_failed.txt'].forEach(filename => {
        const filePath = path.join(basePath, filename);
        fs.writeFileSync(filePath, '');
    });
    return true;
});

// Helper: tính dung lượng folder
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
            } catch (e) { }
        }
    } catch (e) { }
    return totalSize;
}

// Lấy dung lượng Puppeteer temp folders
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
                    if (stats.isDirectory()) totalSize += getFolderSize(itemPath);
                    else totalSize += stats.size;
                } catch (e) { }
            }
        }
    } catch (e) { }
    return {
        sizeBytes: totalSize,
        sizeMB: Math.round(totalSize / 1024 / 1024 * 100) / 100,
        folderCount
    };
});

// Xóa Puppeteer temp folders
ipcMain.handle('clear-temp', async () => {
    const tempPath = path.join(process.env.LOCALAPPDATA || '', 'Temp');
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

// Lấy tổng dung lượng cache
ipcMain.handle('get-cache-size', async () => {
    const puppeteerCache = path.join(process.env.USERPROFILE || '', '.cache', 'puppeteer');
    const chromiumData = path.join(process.env.LOCALAPPDATA || '', 'Chromium');
    let totalSize = getFolderSize(puppeteerCache) + getFolderSize(chromiumData);
    return {
        sizeMB: Math.round(totalSize / 1024 / 1024 * 100) / 100,
        sizeBytes: totalSize
    };
});

// Xóa tất cả cache
ipcMain.handle('clear-all-cache', async () => {
    const puppeteerCache = path.join(process.env.USERPROFILE || '', '.cache', 'puppeteer');
    const chromiumData = path.join(process.env.LOCALAPPDATA || '', 'Chromium');
    const tempPath = path.join(process.env.LOCALAPPDATA || '', 'Temp');
    let freedSize = 0;
    let deletedCount = 0;

    // Xóa puppeteer cache
    try {
        if (fs.existsSync(puppeteerCache)) {
            freedSize += getFolderSize(puppeteerCache);
            fs.rmSync(puppeteerCache, { recursive: true, force: true });
            deletedCount++;
        }
    } catch (e) { }

    // Xóa Chromium user data
    try {
        if (fs.existsSync(chromiumData)) {
            freedSize += getFolderSize(chromiumData);
            fs.rmSync(chromiumData, { recursive: true, force: true });
            deletedCount++;
        }
    } catch (e) { }

    // Xóa puppeteer temp folders
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
