const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

// Import check worker
const { CheckWorker, detectAllBrowsers } = require('./check_worker');

let mainWindow;
let checkWorker;
let selectedBrowserId = null; // Lưu browser đã chọn

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
        icon: path.join(__dirname, 'icon.ico'),
        title: 'GG Check Account',
        backgroundColor: '#1a1a2e'
    });

    mainWindow.loadFile('index.html');

    // Uncomment to open DevTools
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

// Detect tất cả browsers trên máy
ipcMain.handle('detect-browsers', async () => {
    return detectAllBrowsers();
});

// Set browser để dùng
ipcMain.handle('set-browser', async (event, browserId) => {
    selectedBrowserId = browserId;
    console.log('🌐 Selected browser:', selectedBrowserId);
    return true;
});

// Bắt đầu chạy
ipcMain.handle('start-login', async (event, data) => {
    const accounts = Array.isArray(data) ? data : data.accounts;
    const options = data.options || {};
    checkWorker = new CheckWorker(mainWindow, selectedBrowserId, options);
    return await checkWorker.startCheck(accounts);
});

ipcMain.handle('stop-login', async () => {
    if (checkWorker) {
        await checkWorker.stop();
    }
    return true;
});

// Đóng tất cả browsers
ipcMain.handle('close-all-browsers', async () => {
    if (checkWorker) {
        await checkWorker.closeAllBrowsers();
    }
    return true;
});

// Xác định basePath cho cả dev và production
function getBasePath() {
    if (process.env.PORTABLE_EXECUTABLE_DIR) {
        return process.env.PORTABLE_EXECUTABLE_DIR;
    } else if (process.resourcesPath && !process.resourcesPath.includes('node_modules')) {
        return path.dirname(process.resourcesPath);
    } else {
        return __dirname;
    }
}

// Đọc file kết quả
ipcMain.handle('read-results', async () => {
    const basePath = getBasePath();

    const readFile = (filename) => {
        const filePath = path.join(basePath, filename);
        if (fs.existsSync(filePath)) {
            return fs.readFileSync(filePath, 'utf8').trim();
        }
        return '';
    };

    return {
        loginOk: readFile('login_ok.txt'),
        loginFailed: readFile('login_failed.txt'),
        need2fa: readFile('need_2fa.txt')
    };
});

// Lưu file
ipcMain.handle('save-file', async (event, { filename, content }) => {
    const filePath = path.join(__dirname, filename);
    fs.writeFileSync(filePath, content);
    return true;
});

// Import file
ipcMain.handle('import-file', async (event, filePath) => {
    if (fs.existsSync(filePath)) {
        return fs.readFileSync(filePath, 'utf8');
    }
    return '';
});

// Clear all result files
ipcMain.handle('clear-results', async () => {
    const basePath = getBasePath();
    const files = ['login_ok.txt', 'need_2fa.txt', 'login_failed.txt', 'check_results.json'];

    files.forEach(filename => {
        const filePath = path.join(basePath, filename);
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
        }
        // Tạo file trống mới
        if (filename === 'check_results.json') {
            fs.writeFileSync(filePath, '[]');
        } else {
            fs.writeFileSync(filePath, '');
        }
    });

    return true;
});

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
                    if (stats.isDirectory()) {
                        // Tính size folder (recursive)
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

// Xóa Puppeteer temp folders
ipcMain.handle('clear-temp', async () => {
    const tempPath = path.join(process.env.LOCALAPPDATA || '', 'Temp');
    let deletedCount = 0;
    let freedSize = 0;

    try {
        const items = fs.readdirSync(tempPath);
        for (const item of items) {
            if (item.startsWith('puppeteer')) {
                const itemPath = path.join(tempPath, item);
                try {
                    // Tính size trước khi xóa
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

// Xác định đường dẫn chromium folder
function getChromiumPath() {
    if (process.resourcesPath) {
        return path.join(process.resourcesPath, 'chromium');
    }
    return path.join(__dirname, 'chromium');
}

// Check browser exists
ipcMain.handle('check-browser-exists', async () => {
    const chromiumPath = getChromiumPath();
    const chromePath = path.join(chromiumPath, 'chrome.exe');

    return {
        exists: fs.existsSync(chromePath),
        path: chromiumPath
    };
});

// Download browser (Chromium)
ipcMain.handle('download-browser', async () => {
    const chromiumPath = getChromiumPath();

    try {
        // Dùng @puppeteer/browsers để download
        const { install, Browser, resolveBuildId } = require('@puppeteer/browsers');

        // Tạo folder nếu chưa có
        if (!fs.existsSync(chromiumPath)) {
            fs.mkdirSync(chromiumPath, { recursive: true });
        }

        mainWindow.webContents.send('download-progress', {
            status: 'Đang tải Chromium...',
            percent: 0
        });

        const buildId = await resolveBuildId(Browser.CHROME, 'stable', 'stable');

        const result = await install({
            cacheDir: chromiumPath,
            browser: Browser.CHROME,
            buildId: buildId,
            downloadProgressCallback: (downloadedBytes, totalBytes) => {
                const percent = Math.round((downloadedBytes / totalBytes) * 100);
                mainWindow.webContents.send('download-progress', {
                    status: `Đang tải... ${Math.round(downloadedBytes / 1024 / 1024)}MB / ${Math.round(totalBytes / 1024 / 1024)}MB`,
                    percent
                });
            }
        });

        mainWindow.webContents.send('download-progress', {
            status: 'Hoàn thành!',
            percent: 100
        });

        return { success: true, path: result.executablePath };
    } catch (error) {
        mainWindow.webContents.send('download-progress', {
            status: `Lỗi: ${error.message}`,
            percent: 0
        });
        return { success: false, error: error.message };
    }
});

// Helper function để tính dung lượng folder
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

// Lấy tổng dung lượng cache
ipcMain.handle('get-cache-size', async () => {
    const puppeteerCache = path.join(process.env.USERPROFILE || '', '.cache', 'puppeteer');
    const chromiumData = path.join(process.env.LOCALAPPDATA || '', 'Chromium');

    let totalSize = 0;
    totalSize += getFolderSize(puppeteerCache);
    totalSize += getFolderSize(chromiumData);

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
            console.log('Deleted puppeteer cache');
        }
    } catch (e) {
        console.log('Error deleting puppeteer cache:', e.message);
    }

    // Xóa Chromium user data
    try {
        if (fs.existsSync(chromiumData)) {
            freedSize += getFolderSize(chromiumData);
            fs.rmSync(chromiumData, { recursive: true, force: true });
            deletedCount++;
            console.log('Deleted Chromium data');
        }
    } catch (e) {
        console.log('Error deleting Chromium data:', e.message);
    }

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
