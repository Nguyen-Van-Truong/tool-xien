const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    // Bắt đầu login
    startLogin: (accounts, options = {}) => ipcRenderer.invoke('start-login', { accounts, options }),

    // Dừng login
    stopLogin: () => ipcRenderer.invoke('stop-login'),

    // Detect browsers trên máy
    detectBrowsers: () => ipcRenderer.invoke('detect-browsers'),

    // Set browser để dùng
    setBrowser: (browserId) => ipcRenderer.invoke('set-browser', browserId),

    // Đọc kết quả
    readResults: () => ipcRenderer.invoke('read-results'),

    // Xóa kết quả
    clearResults: () => ipcRenderer.invoke('clear-results'),

    // Đóng tất cả browsers
    closeAllBrowsers: () => ipcRenderer.invoke('close-all-browsers'),

    // Lưu file
    saveFile: (filename, content) => ipcRenderer.invoke('save-file', { filename, content }),

    // Import file
    importFile: (filePath) => ipcRenderer.invoke('import-file', filePath),

    // Nhận log từ main process
    onLog: (callback) => ipcRenderer.on('log', (event, data) => callback(data)),

    // Nhận kết quả realtime
    onResult: (callback) => ipcRenderer.on('result', (event, data) => callback(data)),

    // Nhận progress update
    onProgress: (callback) => ipcRenderer.on('progress', (event, data) => callback(data)),

    // Hoàn thành
    onComplete: (callback) => ipcRenderer.on('complete', (event, data) => callback(data)),

    // Lấy dung lượng Puppeteer temp
    getTempSize: () => ipcRenderer.invoke('get-temp-size'),

    // Xóa Puppeteer temp
    clearTemp: () => ipcRenderer.invoke('clear-temp'),

    // Download browser
    downloadBrowser: () => ipcRenderer.invoke('download-browser'),

    // Check browser exists
    checkBrowserExists: () => ipcRenderer.invoke('check-browser-exists'),

    // Nhận download progress
    onDownloadProgress: (callback) => ipcRenderer.on('download-progress', (event, data) => callback(data))
});
