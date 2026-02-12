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
        loginFailed: readFile('login_failed.txt')
    };
});

ipcMain.handle('clear-results', async () => {
    const basePath = getBasePath();
    ['passed.txt', 'login_failed.txt'].forEach(filename => {
        const filePath = path.join(basePath, filename);
        fs.writeFileSync(filePath, '');
    });
    return true;
});
