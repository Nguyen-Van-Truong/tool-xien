const http = require('http');
const ppt = require('./node_modules/puppeteer-core');

(async () => {
    const r = await new Promise((res, rej) => {
        http.get('http://127.0.0.1:61623/json/version', r => {
            let d = ''; r.on('data', c => d += c);
            r.on('end', () => res(JSON.parse(d)));
        }).on('error', rej);
    });

    const b = await ppt.connect({ browserWSEndpoint: r.webSocketDebuggerUrl, defaultViewport: null });
    const pp = await b.pages();
    const p = pp[0];

    console.log('URL:', p.url());

    // Inspect first card shadow DOM
    const info = await p.evaluate(() => {
        const app = document.querySelector('profile-picker-app');
        const mv = app.shadowRoot.querySelector('profile-picker-main-view');
        const card = mv.shadowRoot.querySelector('profile-card[data-index="0"]');
        if (!card || !card.shadowRoot) return 'no shadow';
        const sr = card.shadowRoot;
        const html = sr.innerHTML;
        const tags = [...sr.querySelectorAll('*')].map(e => `${e.tagName}.${e.className}`).join('\n');
        return { html: html.substring(0, 2000), tags, text: sr.textContent.trim() };
    });

    console.log(JSON.stringify(info, null, 2));

    // Get all card names
    const names = await p.evaluate(() => {
        const app = document.querySelector('profile-picker-app');
        const mv = app.shadowRoot.querySelector('profile-picker-main-view');
        const cards = mv.shadowRoot.querySelectorAll('profile-card');
        return [...cards].map(card => {
            const idx = card.getAttribute('data-index');
            const sr = card.shadowRoot;
            if (!sr) return { idx, name: '?' };
            // Try different selectors
            const nameEl = sr.querySelector('.profile-card-name, .name, [class*=name], .profile-name, h3, span');
            const text = sr.textContent.trim();
            return { idx, name: nameEl ? nameEl.textContent.trim() : text.substring(0, 30) };
        });
    });

    console.log('\n=== PROFILE NAMES ===');
    for (const n of names) console.log(`  [${n.idx}] ${n.name}`);

    // Try clicking card 0
    console.log('\n=== TRYING CLICK ===');
    await p.evaluate(() => {
        const app = document.querySelector('profile-picker-app');
        const mv = app.shadowRoot.querySelector('profile-picker-main-view');
        const card = mv.shadowRoot.querySelector('profile-card[data-index="1"]');
        if (card) card.click();
    });

    // Wait for new page
    await new Promise(r => setTimeout(r, 3000));
    const pages2 = await b.pages();
    console.log('Pages after click:', pages2.length);
    for (const pg of pages2) {
        console.log('  Page:', pg.url());
    }

    b.disconnect();
    process.exit(0);
})().catch(e => { console.error(e.message); process.exit(1); });
