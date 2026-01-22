const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

// Import flow worker
const { FlowWorker, detectAllBrowsers } = require('./flow_worker');

let mainWindow;
let flowWorker;
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
        title: 'Google Flow Login V3',
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
    // data = { accounts, options: { headless, ramFlags } }
    const accounts = Array.isArray(data) ? data : data.accounts;
    const options = data.options || {};
    flowWorker = new FlowWorker(mainWindow, selectedBrowserId, options);
    return await flowWorker.start(accounts);
});

// Dừng
ipcMain.handle('stop-login', async () => {
    if (flowWorker) {
        await flowWorker.stop();
    }
    return true;
});

// Đóng tất cả browsers
ipcMain.handle('close-all-browsers', async () => {
    if (flowWorker) {
        await flowWorker.closeAllBrowsers();
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
        hasFlow: readFile('has_flow.txt'),
        noFlow: readFile('no_flow.txt'),
        loginFailed: readFile('login_failed.txt')
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
    const files = ['has_flow.txt', 'no_flow.txt', 'login_failed.txt', 'flow_results.json'];

    files.forEach(filename => {
        const filePath = path.join(basePath, filename);
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
        }
        // Tạo file trống mới
        if (filename === 'flow_results.json') {
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
