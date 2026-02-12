const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    startLogin: (accounts, options = {}) => ipcRenderer.invoke('start-login', { accounts, options }),
    stopLogin: () => ipcRenderer.invoke('stop-login'),
    detectBrowsers: () => ipcRenderer.invoke('detect-browsers'),
    setBrowser: (browserId) => ipcRenderer.invoke('set-browser', browserId),
    readResults: () => ipcRenderer.invoke('read-results'),
    clearResults: () => ipcRenderer.invoke('clear-results'),
    closeAllBrowsers: () => ipcRenderer.invoke('close-all-browsers'),

    onLog: (callback) => ipcRenderer.on('log', (event, data) => callback(data)),
    onResult: (callback) => ipcRenderer.on('result', (event, data) => callback(data)),
    onProgress: (callback) => ipcRenderer.on('progress', (event, data) => callback(data)),
    onComplete: (callback) => ipcRenderer.on('complete', (event, data) => callback(data))
});
