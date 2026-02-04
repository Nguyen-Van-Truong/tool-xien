/**
 * Puppeteer configuration
 * Caches browser downloads locally to avoid re-downloading
 */
module.exports = {
    cacheDirectory: './.puppeteer-cache',
    downloadBaseUrl: 'https://storage.googleapis.com/chrome-for-testing-public'
};
