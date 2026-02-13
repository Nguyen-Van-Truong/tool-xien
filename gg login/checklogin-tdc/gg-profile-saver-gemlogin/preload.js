const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    // GemLogin
    checkGemLogin: () => ipcRenderer.invoke('check-gemlogin'),
    getGemLoginProfiles: () => ipcRenderer.invoke('get-gemlogin-profiles'),
    setGemLoginProfile: (id) => ipcRenderer.invoke('set-gemlogin-profile', id),

    // Login
    startLogin: (accounts, options = {}) => ipcRenderer.invoke('start-login', { accounts, options }),
    stopLogin: () => ipcRenderer.invoke('stop-login'),
    closeAllBrowsers: () => ipcRenderer.invoke('close-all-browsers'),

    // Profiles
    getProfiles: () => ipcRenderer.invoke('get-profiles'),
    openProfile: (email) => ipcRenderer.invoke('open-profile', email),
    openAllProfiles: () => ipcRenderer.invoke('open-all-profiles'),
    deleteProfile: (email) => ipcRenderer.invoke('delete-profile', email),
    cleanProfiles: () => ipcRenderer.invoke('clean-profiles'),

    // Import
    importAccounts: () => ipcRenderer.invoke('import-accounts'),

    // Accounts file
    readAccounts: () => ipcRenderer.invoke('read-accounts'),
    saveAccounts: (content) => ipcRenderer.invoke('save-accounts', content),

    // Backup / Restore
    backup: () => ipcRenderer.invoke('backup'),
    listBackups: () => ipcRenderer.invoke('list-backups'),
    restore: (name) => ipcRenderer.invoke('restore', name),

    // Events
    onLog: (cb) => ipcRenderer.on('log', (e, data) => cb(data)),
    onResult: (cb) => ipcRenderer.on('result', (e, data) => cb(data)),
    onProgress: (cb) => ipcRenderer.on('progress', (e, data) => cb(data)),
    onComplete: (cb) => ipcRenderer.on('complete', (e, data) => cb(data)),
    onProfilesUpdated: (cb) => ipcRenderer.on('profiles-updated', () => cb()),
});
