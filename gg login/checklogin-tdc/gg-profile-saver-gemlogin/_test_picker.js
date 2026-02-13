// Test CDP interaction with GemLogin profile picker
const puppeteer = require('puppeteer-core');
const http = require('http');

const DEBUG_ADDR = process.argv[2] || '127.0.0.1:56509';

function getJson(url) {
    return new Promise((resolve, reject) => {
        http.get(url, (res) => {
            let data = '';
            res.on('data', c => data += c);
            res.on('end', () => resolve(JSON.parse(data)));
        }).on('error', reject);
    });
}

async function main() {
    console.log(`Connecting to ${DEBUG_ADDR}...`);
    
    // Get WebSocket URL
    const version = await getJson(`http://${DEBUG_ADDR}/json/version`);
    console.log('Browser:', version.Browser);
    
    const browser = await puppeteer.connect({
        browserWSEndpoint: version.webSocketDebuggerUrl,
        defaultViewport: null,
    });

    const pages = await browser.pages();
    console.log(`Found ${pages.length} pages`);
    
    const pickerPage = pages.find(p => p.url().includes('profile-picker'));
    if (!pickerPage) {
        console.log('No profile picker page found!');
        return;
    }
    
    console.log('Profile picker found:', pickerPage.url());
    
    // Try to get profile cards through Shadow DOM
    const profiles = await pickerPage.evaluate(() => {
        const results = [];
        
        // Profile picker uses nested Shadow DOMs
        const app = document.querySelector('profile-picker-app');
        if (!app || !app.shadowRoot) return { error: 'No app shadowRoot', html: document.body.innerHTML.substring(0, 500) };
        
        const mainView = app.shadowRoot.querySelector('profile-picker-main-view');
        if (!mainView || !mainView.shadowRoot) return { error: 'No mainView shadowRoot', appHTML: app.shadowRoot.innerHTML.substring(0, 500) };
        
        const cards = mainView.shadowRoot.querySelectorAll('profile-card');
        for (const card of cards) {
            const sr = card.shadowRoot;
            if (!sr) {
                results.push({ index: card.dataset.index, name: '(no shadowRoot)' });
                continue;
            }
            // Try to find name element
            const nameEl = sr.querySelector('.profile-card-name') 
                || sr.querySelector('[id*="name"]')
                || sr.querySelector('span')
                || sr.querySelector('div');
            
            results.push({
                index: card.dataset.index,
                name: nameEl ? nameEl.textContent.trim() : '(no name found)',
                innerHTML: sr.innerHTML.substring(0, 300),
            });
        }
        
        return { count: cards.length, profiles: results };
    });
    
    console.log('Profiles:', JSON.stringify(profiles, null, 2));
    
    // Try clicking profile at index 0 (github1)
    if (profiles.count > 0) {
        console.log('\n--- Trying to click profile at index 1 (github2) ---');
        
        const clicked = await pickerPage.evaluate((targetIndex) => {
            const app = document.querySelector('profile-picker-app');
            if (!app?.shadowRoot) return 'no app';
            const mainView = app.shadowRoot.querySelector('profile-picker-main-view');
            if (!mainView?.shadowRoot) return 'no mainView';
            const cards = mainView.shadowRoot.querySelectorAll('profile-card');
            if (targetIndex >= cards.length) return 'index out of range';
            
            const card = cards[targetIndex];
            card.click();
            return 'clicked';
        }, 1);
        
        console.log('Click result:', clicked);
        
        // Wait for new window/page
        await new Promise(r => setTimeout(r, 3000));
        
        // Check targets again
        const targets = await getJson(`http://${DEBUG_ADDR}/json`);
        console.log('\nTargets after click:');
        for (const t of targets) {
            console.log(`  Type: ${t.type} | URL: ${t.url} | Title: ${t.title}`);
        }
        
        const newPages = await browser.pages();
        console.log(`\nPages after click: ${newPages.length}`);
        for (const p of newPages) {
            console.log(`  URL: ${p.url()}`);
        }
    }
    
    browser.disconnect();
}

main().catch(console.error);
