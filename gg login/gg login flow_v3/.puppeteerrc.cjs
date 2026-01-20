/**
 * Puppeteer Configuration
 * Chuyển cache từ ổ C sang folder hiện tại
 */

const path = require('path');

module.exports = {
    // Lưu cache Puppeteer vào folder hiện tại thay vì C:\Users\.cache
    cacheDirectory: path.join(__dirname, '.puppeteer-cache'),
};
