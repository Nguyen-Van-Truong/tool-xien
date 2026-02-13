const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

const { ProfileWorker, checkGemLoginRunning, getGemLoginProfiles } = require('./worker');

let mainWindow;
let worker;
let selectedGemLoginProfileId = null;

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
        title: 'GG Profile Saver (GemLogin)',
        backgroundColor: '#0f0f1a'
    });
    mainWindow.loadFile('index.html');
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });

// ======================== IPC HANDLERS ========================

// ---- GemLogin ----
ipcMain.handle('check-gemlogin', async () => {
    const running = await checkGemLoginRunning();
    return { running };
});

ipcMain.handle('get-gemlogin-profiles', async () => {
    try {
        const profiles = await getGemLoginProfiles();
        return { success: true, profiles };
    } catch (e) {
        return { success: false, error: e.message };
    }
});

ipcMain.handle('set-gemlogin-profile', async (event, id) => {
    selectedGemLoginProfileId = id;
    return true;
});

// ---- Login All ----
ipcMain.handle('start-login', async (event, data) => {
    const accounts = data.accounts;
    const options = data.options || {};
    if (!selectedGemLoginProfileId) {
        mainWindow.webContents.send('log', { message: '❌ Chưa chọn GemLogin profile!', type: 'error' });
        mainWindow.webContents.send('complete', { total: 0, loggedIn: 0, failed: 0, skipped: 0, totalTime: 0 });
        return false;
    }
    worker = new ProfileWorker(mainWindow, { ...options, gemloginProfileId: selectedGemLoginProfileId });
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
    if (!worker) worker = new ProfileWorker(mainWindow, { gemloginProfileId: selectedGemLoginProfileId });
    return await worker.openProfile(email);
});

ipcMain.handle('open-all-profiles', async () => {
    if (!worker) worker = new ProfileWorker(mainWindow, { gemloginProfileId: selectedGemLoginProfileId });
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
