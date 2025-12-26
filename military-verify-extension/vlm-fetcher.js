/**
 * VLM API Fetcher - Fetch all veterans who died in 2025
 * 
 * API: POST https://www.vlm.cem.va.gov/api/v1.1/gcio/profile/search/advanced
 * 
 * Usage: 
 *   node vlm-fetcher.js
 *   
 * Output: veterans_2025.txt with format:
 *   FirstName|LastName|Branch|BirthMonth|BirthDay|BirthYear|DeathMonth|DeathDay|DeathYear
 */

const https = require('https');
const fs = require('fs');

// Config
const LETTERS = 'abcdefghijklmnopqrstuvwxyz'.split('');
const DOD_FROM = '2025-01-01';
const DOD_TO = '2025-12-31';
const LIMIT = 100; // Max per page
const OUTPUT_FILE = 'veterans_2025.txt';

// Month mapping
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];

function parseDate(dateStr) {
    if (!dateStr) return { month: 'January', day: '1', year: '2025' };
    const date = new Date(dateStr);
    return {
        month: MONTHS[date.getMonth()] || 'January',
        day: date.getDate().toString(),
        year: date.getFullYear().toString()
    };
}

function parseBranch(branchCode) {
    const map = {
        'A': 'Army',
        'F': 'Air Force',
        'N': 'Navy',
        'M': 'Marine Corps',
        'C': 'Coast Guard',
        'S': 'Space Force'
    };
    return map[branchCode] || branchCode || 'Navy';
}

function fetchPage(lastName, page) {
    return new Promise((resolve, reject) => {
        const payload = JSON.stringify({
            lastName: lastName,
            dodFrom: DOD_FROM,
            dodTo: DOD_TO,
            orderby: 'date_of_death',
            limit: LIMIT,
            page: page
        });

        const options = {
            hostname: 'www.vlm.cem.va.gov',
            port: 443,
            path: '/api/v1.1/gcio/profile/search/advanced',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(payload),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
                'Accept': 'application/json',
                'Origin': 'https://www.vlm.cem.va.gov',
                'Referer': 'https://www.vlm.cem.va.gov/'
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const json = JSON.parse(data);
                    resolve(json);
                } catch (e) {
                    reject(new Error(`Parse error: ${e.message}`));
                }
            });
        });

        req.on('error', reject);
        req.write(payload);
        req.end();
    });
}

async function fetchAllForLetter(letter) {
    const veterans = [];
    let page = 1;
    let hasMore = true;

    console.log(`Fetching letter "${letter.toUpperCase()}"...`);

    while (hasMore) {
        try {
            const response = await fetchPage(letter, page);

            if (response.profiles && response.profiles.length > 0) {
                for (const profile of response.profiles) {
                    const dob = parseDate(profile.dob);
                    const dod = parseDate(profile.dod);

                    // Parse name
                    const fullName = profile.full_name || '';
                    const nameParts = fullName.trim().split(' ');
                    const firstName = nameParts[0] || '';
                    const lastName = nameParts.slice(1).join(' ') || '';

                    const branch = parseBranch(profile.branch_code);

                    veterans.push({
                        firstName,
                        lastName,
                        branch,
                        birthMonth: dob.month,
                        birthDay: dob.day,
                        birthYear: dob.year,
                        deathMonth: dod.month,
                        deathDay: dod.day,
                        deathYear: dod.year
                    });
                }

                console.log(`  Page ${page}: ${response.profiles.length} records`);

                if (response.profiles.length < LIMIT) {
                    hasMore = false;
                } else {
                    page++;
                    // Rate limiting
                    await new Promise(r => setTimeout(r, 200));
                }
            } else {
                hasMore = false;
            }
        } catch (error) {
            console.error(`  Error on page ${page}: ${error.message}`);
            hasMore = false;
        }
    }

    console.log(`  Total for "${letter.toUpperCase()}": ${veterans.length}`);
    return veterans;
}

function formatVeteran(vet) {
    return `${vet.firstName}|${vet.lastName}|${vet.branch}|${vet.birthMonth}|${vet.birthDay}|${vet.birthYear}|${vet.deathMonth}|${vet.deathDay}|${vet.deathYear}`;
}

async function main() {
    console.log('=== VLM Veteran Fetcher ===');
    console.log(`Date range: ${DOD_FROM} to ${DOD_TO}`);
    console.log(`Output: ${OUTPUT_FILE}\n`);

    const allVeterans = [];

    for (const letter of LETTERS) {
        const veterans = await fetchAllForLetter(letter);
        allVeterans.push(...veterans);

        // Rate limiting between letters
        await new Promise(r => setTimeout(r, 500));
    }

    console.log(`\n=== Total: ${allVeterans.length} veterans ===`);

    // Write to file
    const lines = allVeterans.map(formatVeteran);
    fs.writeFileSync(OUTPUT_FILE, lines.join('\n'), 'utf8');

    console.log(`Saved to ${OUTPUT_FILE}`);
}

main().catch(console.error);
