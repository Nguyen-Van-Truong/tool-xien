/**
 * Preload Script - Context Bridge
 * Exposes safe IPC methods to renderer
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    // Core operations
    startProcess: (accounts, cards, options) => ipcRenderer.invoke('start-process', accounts, cards, options),
    stopProcess: () => ipcRenderer.invoke('stop-process'),
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
    onBrowserCount: (callback) => ipcRenderer.on('browser-count', (_, data) => callback(data))
});
