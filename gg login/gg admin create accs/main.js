const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

// Import admin worker
const AdminWorker = require('./admin_worker');

let mainWindow;
let adminWorker;

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
        title: 'Google Admin Create Accounts',
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

// Bắt đầu tạo accounts
ipcMain.handle('start-create', async (event, config) => {
    adminWorker = new AdminWorker(mainWindow);
    // Pass selected browser ID
    config.browserId = selectedBrowserId;
    return await adminWorker.start(config);
});

// Dừng
ipcMain.handle('stop-create', async () => {
    if (adminWorker) {
        await adminWorker.stop();
    }
    return true;
});

// Đóng browser
ipcMain.handle('close-browser', async () => {
    if (adminWorker) {
        await adminWorker.closeBrowser();
    }
    return true;
});

// Manual login continue - user clicked "Đã đăng nhập xong"
ipcMain.handle('manual-login-continue', async () => {
    if (adminWorker) {
        adminWorker.resolveManualLogin();
    }
    return true;
});

// Selected browser ID
let selectedBrowserId = 'puppeteer';

// Detect available browsers
ipcMain.handle('detect-browsers', async () => {
    const AdminWorker = require('./admin_worker');
    return AdminWorker.detectBrowsers();
});

// Set browser to use
ipcMain.handle('set-browser', async (event, browserId) => {
    selectedBrowserId = browserId;
    console.log(`🌐 Selected browser: ${browserId}`);
    return true;
});

// Resume create - tiếp tục từ trạng thái hiện tại
ipcMain.handle('resume-create', async (event, config) => {
    if (!adminWorker) {
        adminWorker = new AdminWorker(mainWindow);
    }
    // Pass selected browser ID
    config.browserId = selectedBrowserId;
    return await adminWorker.resume(config);
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
        created: readFile('created_accounts.txt'),
        failed: readFile('failed_accounts.txt')
    };
});

// Lưu file
ipcMain.handle('save-file', async (event, { filename, content }) => {
    const filePath = path.join(__dirname, filename);
    fs.writeFileSync(filePath, content);
    return true;
});

// Clear all result files
ipcMain.handle('clear-results', async () => {
    const basePath = getBasePath();
    const files = ['created_accounts.txt', 'failed_accounts.txt', 'admin_results.json'];

    files.forEach(filename => {
        const filePath = path.join(basePath, filename);
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
        }
        if (filename === 'admin_results.json') {
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
