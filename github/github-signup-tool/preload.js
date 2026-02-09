/**
 * Preload Script - Context Bridge
 * Exposes safe IPC methods to renderer
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    // Core operations
    startSignup: (accounts, options) => ipcRenderer.invoke('start-signup', accounts, options),
    stopSignup: () => ipcRenderer.invoke('stop-signup'),
    nextAccount: (status) => ipcRenderer.invoke('next-account', status),
    closeAllBrowsers: () => ipcRenderer.invoke('close-all-browsers'),

    // Results
    readResults: () => ipcRenderer.invoke('read-results'),
    clearResults: () => ipcRenderer.invoke('clear-results'),

    // Temp management
    getTempSize: () => ipcRenderer.invoke('get-temp-size'),
    deleteBrowserData: () => ipcRenderer.invoke('delete-browser-data'),

    // Event listeners
    onLog: (callback) => ipcRenderer.on('log', (_, data) => callback(data)),
    onResult: (callback) => ipcRenderer.on('result', (_, data) => callback(data)),
    onProgress: (callback) => ipcRenderer.on('progress', (_, data) => callback(data)),
    onComplete: (callback) => ipcRenderer.on('complete', (_, data) => callback(data)),
    onWaitingManual: (callback) => ipcRenderer.on('waiting-manual', (_, data) => callback(data)),
    onBrowserCount: (callback) => ipcRenderer.on('browser-count', (_, data) => callback(data)),
    onOTPStatus: (callback) => ipcRenderer.on('otp-status', (_, data) => callback(data))
});
