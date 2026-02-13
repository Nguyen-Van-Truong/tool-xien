const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    // Browser
    detectBrowsers: () => ipcRenderer.invoke('detect-browsers'),
    setBrowser: (id) => ipcRenderer.invoke('set-browser', id),
    downloadBrowser: () => ipcRenderer.invoke('download-browser'),

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

    // Temp & Cache
    getProfilesSize: () => ipcRenderer.invoke('get-profiles-size'),
    getTempSize: () => ipcRenderer.invoke('get-temp-size'),
    clearTemp: () => ipcRenderer.invoke('clear-temp'),

    // Rename
    renameProfile: (email, newName) => ipcRenderer.invoke('rename-profile', email, newName),

    // Reorder
    reorderProfile: (email, direction) => ipcRenderer.invoke('reorder-profile', email, direction),

    // GitHub
    githubSignup: (emails) => ipcRenderer.invoke('github-signup', emails),
    githubDone: (email, status) => ipcRenderer.invoke('github-done', email, status),

    // Events
    onLog: (cb) => ipcRenderer.on('log', (e, data) => cb(data)),
    onResult: (cb) => ipcRenderer.on('result', (e, data) => cb(data)),
    onProgress: (cb) => ipcRenderer.on('progress', (e, data) => cb(data)),
    onComplete: (cb) => ipcRenderer.on('complete', (e, data) => cb(data)),
    onProfilesUpdated: (cb) => ipcRenderer.on('profiles-updated', () => cb()),
    onGithubWaiting: (cb) => ipcRenderer.on('github-waiting', (e, data) => cb(data)),
});
