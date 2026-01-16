const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

// Import flow worker
const FlowWorker = require('./flow_worker');

let mainWindow;
let flowWorker;

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

// Bắt đầu chạy
ipcMain.handle('start-login', async (event, accounts) => {
    flowWorker = new FlowWorker(mainWindow);
    return await flowWorker.start(accounts);
});

// Dừng
ipcMain.handle('stop-login', async () => {
    if (flowWorker) {
        await flowWorker.stop();
    }
    return true;
});

// Đọc file kết quả
ipcMain.handle('read-results', async () => {
    const basePath = __dirname;

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
    const basePath = __dirname;
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
