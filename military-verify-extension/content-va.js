// Content script for VLM.cem.va.gov - Scrape veteran data

console.log('Military Verify Extension: VLM content script loaded');

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'scrapeVeterans') {
        const data = scrapeVeteransList();
        sendResponse({ data });
    }
    return true;
});

// Month name mapping
const MONTH_MAP = {
    'jan': 'January', 'feb': 'February', 'mar': 'March', 'apr': 'April',
    'may': 'May', 'jun': 'June', 'jul': 'July', 'aug': 'August',
    'sep': 'September', 'oct': 'October', 'nov': 'November', 'dec': 'December',
    '01': 'January', '02': 'February', '03': 'March', '04': 'April',
    '05': 'May', '06': 'June', '07': 'July', '08': 'August',
    '09': 'September', '10': 'October', '11': 'November', '12': 'December'
};

function parseMonth(monthStr) {
    if (!monthStr) return 'January';
    const key = monthStr.toLowerCase().substring(0, 3);
    return MONTH_MAP[key] || monthStr;
}

function parseDate(dateStr) {
    // Handle formats: "MM-DD-YYYY", "Jan 1, 2025", "01-15-2025"
    if (!dateStr) return { month: 'January', day: '1', year: '2025' };

    // MM-DD-YYYY format
    const dashMatch = dateStr.match(/(\d{1,2})-(\d{1,2})-(\d{4})/);
    if (dashMatch) {
        return {
            month: MONTH_MAP[dashMatch[1].padStart(2, '0')] || 'January',
            day: dashMatch[2],
            year: dashMatch[3]
        };
    }

    // Month DD, YYYY format (e.g., "Jul 19, 1946")
    const textMatch = dateStr.match(/([A-Za-z]+)\s*(\d{1,2}),?\s*(\d{4})/);
    if (textMatch) {
        return {
            month: parseMonth(textMatch[1]),
            day: textMatch[2],
            year: textMatch[3]
        };
    }

    return { month: 'January', day: '1', year: '2025' };
}

function parseBranch(branchText) {
    if (!branchText) return 'Navy';
    const upper = branchText.toUpperCase();
    if (upper.includes('NAVY')) return 'Navy';
    if (upper.includes('ARMY')) return 'Army';
    if (upper.includes('AIR')) return 'Air Force';
    if (upper.includes('MARINE')) return 'Marine Corps';
    if (upper.includes('COAST')) return 'Coast Guard';
    if (upper.includes('SPACE')) return 'Space Force';
    return 'Navy';
}

// Scrape from search results page
function scrapeVeteransList() {
    const veterans = [];

    // Find all veteran cards/items in search results
    // VLM uses various class names, try common patterns
    const cards = document.querySelectorAll('[class*="card"], [class*="result"], [class*="veteran"], [class*="memorial"], a[href*="/"]');

    // Also check for specific VLM structure based on what we saw
    const pageText = document.body.innerText;
    const lines = pageText.split('\n');

    let currentVet = null;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();

        // Look for branch mentions followed by names
        if (line.includes('UNITED STATES') || line.includes('US NAVY') || line.includes('US ARMY') ||
            line.includes('US AIR FORCE') || line.includes('US MARINE') || line.includes('US COAST GUARD')) {
            currentVet = { branch: parseBranch(line) };
            continue;
        }

        // Look for names in ALL CAPS (typical for veteran names)
        if (currentVet && /^[A-Z\s]+$/.test(line) && line.length > 3 && !line.includes('UNITED') && !line.includes('NAVY')) {
            const nameParts = line.split(' ');
            if (nameParts.length >= 2) {
                // First name is first word, last name is rest
                currentVet.firstName = nameParts[0];
                currentVet.lastName = nameParts.slice(1).join(' ');
            }
            continue;
        }

        // Look for dates (MM-DD-YYYY format)
        const dateMatch = line.match(/(\d{2})-(\d{2})-(\d{4})/);
        if (currentVet && currentVet.firstName && dateMatch) {
            // This is likely death date
            const deathDate = parseDate(line);
            currentVet.deathMonth = deathDate.month;
            currentVet.deathDay = deathDate.day;
            currentVet.deathYear = deathDate.year;

            // Estimate birth year (died age 70-90)
            const deathYear = parseInt(currentVet.deathYear);
            const birthYear = deathYear - Math.floor(Math.random() * 20 + 70);
            currentVet.birthMonth = currentVet.deathMonth;
            currentVet.birthDay = Math.floor(Math.random() * 28 + 1).toString();
            currentVet.birthYear = birthYear.toString();

            // Save this veteran and reset
            veterans.push({ ...currentVet });
            currentVet = null;
        }
    }

    // If we found veterans from text parsing, return those
    if (veterans.length > 0) {
        console.log(`Scraped ${veterans.length} veterans from page text`);
        return veterans;
    }

    // Fallback: try to parse structured elements
    cards.forEach(card => {
        try {
            const text = card.textContent || '';
            const vet = {};

            // Extract name
            const nameMatch = text.match(/([A-Z]{2,}\s+)+[A-Z]{2,}/);
            if (nameMatch) {
                const parts = nameMatch[0].trim().split(/\s+/);
                vet.firstName = parts[0];
                vet.lastName = parts.slice(1).join(' ');
            }

            // Extract branch
            vet.branch = parseBranch(text);

            // Extract date
            const dateMatch = text.match(/(\d{2})-(\d{2})-(\d{4})/);
            if (dateMatch) {
                const date = parseDate(dateMatch[0]);
                vet.deathMonth = date.month;
                vet.deathDay = date.day;
                vet.deathYear = date.year;

                // Estimate birth
                const dy = parseInt(vet.deathYear);
                vet.birthYear = (dy - 75).toString();
                vet.birthMonth = date.month;
                vet.birthDay = '1';
            }

            if (vet.firstName && vet.lastName) {
                veterans.push(vet);
            }
        } catch (e) { }
    });

    console.log(`Scraped ${veterans.length} veterans`);
    return veterans;
}

// Add floating scrape button on VLM pages
function addScrapeButton() {
    if (document.querySelector('.military-verify-scrape-btn')) return;

    const btn = document.createElement('button');
    btn.className = 'military-verify-scrape-btn';
    btn.innerHTML = '📥 Scrape Veterans';
    btn.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 999999;
    padding: 12px 20px;
    background: linear-gradient(135deg, #00d9ff, #00ff88);
    color: #000;
    border: none;
    border-radius: 25px;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(0,217,255,0.4);
    font-size: 14px;
  `;

    btn.addEventListener('click', () => {
        const veterans = scrapeVeteransList();
        if (veterans.length > 0) {
            // Format as text
            const text = veterans.map(v =>
                `${v.firstName}|${v.lastName}|${v.branch}|${v.birthMonth || 'January'}|${v.birthDay || '1'}|${v.birthYear || '1950'}|${v.deathMonth || 'January'}|${v.deathDay || '1'}|${v.deathYear || '2025'}`
            ).join('\n');

            // Copy to clipboard
            navigator.clipboard.writeText(text).then(() => {
                btn.innerHTML = `✅ Copied ${veterans.length} veterans!`;
                setTimeout(() => btn.innerHTML = '📥 Scrape Veterans', 2000);
            });
        } else {
            btn.innerHTML = '❌ No veterans found';
            setTimeout(() => btn.innerHTML = '📥 Scrape Veterans', 2000);
        }
    });

    document.body.appendChild(btn);
}

// Initialize
setTimeout(addScrapeButton, 1500);
