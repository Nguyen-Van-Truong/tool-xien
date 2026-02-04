/**
 * Preload Script - IPC Bridge
 * Exposes safe IPC methods to renderer process
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    // Start signup
    startSignup: (accounts, options) => ipcRenderer.invoke('start-signup', accounts, options),

    // Stop signup
    stopSignup: () => ipcRenderer.invoke('stop-signup'),

    // Close all browsers
    closeAllBrowsers: () => ipcRenderer.invoke('close-all-browsers'),

    // Read results
    readResults: () => ipcRenderer.invoke('read-results'),

    // Clear results
    clearResults: () => ipcRenderer.invoke('clear-results'),

    // Event listeners
    onLog: (callback) => ipcRenderer.on('log', (event, data) => callback(data)),
    onProgress: (callback) => ipcRenderer.on('progress', (event, data) => callback(data)),
    onResult: (callback) => ipcRenderer.on('result', (event, data) => callback(data)),
    onComplete: (callback) => ipcRenderer.on('complete', (event, data) => callback(data))
});
