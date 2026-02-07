/**
 * Email Service Module - UPDATED for new tinyhost.shop API
 * Handles temporary email generation and OTP retrieval
 */

const axios = require('axios');

const EMAIL_API_BASE = 'https://tinyhost.shop/api';
const MAX_RETRIES = 12; // 12 attempts x 5s = 60s max wait
const RETRY_DELAY = 5000; // 5 seconds between retries

// Random English name lists for natural-looking emails
const FIRST_NAMES = [
    'james', 'john', 'robert', 'michael', 'david', 'william', 'richard', 'joseph', 'thomas', 'charles',
    'daniel', 'matthew', 'anthony', 'mark', 'steven', 'paul', 'andrew', 'brian', 'kevin', 'jason',
    'mary', 'patricia', 'jennifer', 'linda', 'barbara', 'elizabeth', 'susan', 'jessica', 'sarah', 'karen',
    'emily', 'emma', 'olivia', 'sophia', 'isabella', 'mia', 'charlotte', 'amelia', 'harper', 'evelyn',
    'nathan', 'ryan', 'jacob', 'ethan', 'logan', 'lucas', 'mason', 'alexander', 'henry', 'benjamin',
    'hannah', 'madison', 'chloe', 'grace', 'zoey', 'lily', 'ella', 'riley', 'aria', 'scarlett'
];

const LAST_NAMES = [
    'smith', 'johnson', 'williams', 'brown', 'jones', 'garcia', 'miller', 'davis', 'rodriguez', 'martinez',
    'hernandez', 'lopez', 'gonzalez', 'wilson', 'anderson', 'thomas', 'taylor', 'moore', 'jackson', 'martin',
    'lee', 'perez', 'thompson', 'white', 'harris', 'sanchez', 'clark', 'ramirez', 'lewis', 'robinson',
    'walker', 'young', 'allen', 'king', 'wright', 'scott', 'torres', 'nguyen', 'hill', 'flores',
    'green', 'adams', 'nelson', 'baker', 'hall', 'rivera', 'campbell', 'mitchell', 'carter', 'roberts'
];

/**
 * Generate a random natural-looking username from English names
 * Patterns: firstname.lastname23, firstnamelastname99, f.lastname42, firstname_l56, etc.
 */
function generateNaturalUsername() {
    const first = FIRST_NAMES[Math.floor(Math.random() * FIRST_NAMES.length)];
    const last = LAST_NAMES[Math.floor(Math.random() * LAST_NAMES.length)];
    const num = Math.floor(Math.random() * 999) + 1; // 1-999
    const year = Math.floor(Math.random() * 26) + 85; // 85-10 (birth year style)

    // Randomly pick a pattern
    const patterns = [
        `${first}.${last}${num}`,                          // john.smith42
        `${first}${last}${num}`,                            // johnsmith42
        `${first}_${last}${num}`,                           // john_smith42
        `${first}.${last[0]}${num}`,                        // john.s42
        `${first[0]}${last}${num}`,                         // jsmith42
        `${first}${last}${year}`,                           // johnsmith95
        `${first}.${last}`,                                  // john.smith
        `${first}${num}`,                                    // john42
        `${first}_${last[0]}${num}`,                        // john_s42
        `${first[0]}.${last}${num}`,                        // j.smith42
        `${first}${last.substring(0, 3)}${num}`,            // johnsmi42
        `${first}.${last}${Math.floor(Math.random() * 9)}${Math.floor(Math.random() * 9)}`, // john.smith73
    ];

    return patterns[Math.floor(Math.random() * patterns.length)];
}

/**
 * Generate a temporary email address
 * @returns {Promise<{email: string, domain: string, user: string}>}
 */
async function generateEmail() {
    try {
        console.log('📧 Generating temporary email...');

        // Get random domain from API
        const response = await axios.get(`${EMAIL_API_BASE}/random-domains/`, {
            params: { limit: 5 }
        });

        if (!response.data || !response.data.domains || response.data.domains.length === 0) {
            throw new Error('No domains available from API');
        }

        // Pick random domain
        const domains = response.data.domains;
        const domain = domains[Math.floor(Math.random() * domains.length)];

        // Generate natural-looking username (English names)
        const username = generateNaturalUsername();
        const email = `${username}@${domain}`;

        console.log(`✅ Generated email: ${email}`);
        return { email, domain, user: username };

    } catch (error) {
        console.error('❌ Email generation failed:', error.message);
        throw new Error(`Failed to generate email: ${error.message}`);
    }
}

/**
 * Check email inbox for OTP verification code
 * @param {string} domain - Email domain
 * @param {string} user - Username (without @domain)
 * @returns {Promise<string|null>} OTP code if found, null otherwise
 */
async function checkEmailForCode(domain, user) {
    try {
        console.log(`📬 Checking inbox for ${user}@${domain}...`);

        for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
            console.log(`   Attempt ${attempt}/${MAX_RETRIES}...`);

            try {
                // Fetch inbox using new API format
                const response = await axios.get(`${EMAIL_API_BASE}/email/${domain}/${user}/`, {
                    params: {
                        page: 1,
                        limit: 20
                    },
                    timeout: 10000
                });

                const data = response.data;

                if (!data || !data.emails || data.emails.length === 0) {
                    console.log('   No emails yet...');
                } else {
                    console.log(`   Found ${data.emails.length} email(s)`);

                    // Check each email for verification code
                    for (const mail of data.emails) {
                        const code = extractCodeFromEmail(mail);
                        if (code) {
                            console.log(`✅ Found OTP code: ${code}`);
                            return code;
                        }
                    }
                }

            } catch (fetchError) {
                if (fetchError.response && fetchError.response.status === 404) {
                    console.log('   Inbox not created yet...');
                } else {
                    console.log(`   Fetch error: ${fetchError.message}`);
                }
            }

            // Wait before next attempt (except on last attempt)
            if (attempt < MAX_RETRIES) {
                await sleep(RETRY_DELAY);
            }
        }

        console.log('❌ No verification code found after all attempts');
        return null;

    } catch (error) {
        console.error('❌ Email check failed:', error.message);
        return null;
    }
}

/**
 * Extract OTP code from email content
 * @param {Object} email - Email object with subject/body/html_body
 * @returns {string|null} Extracted code or null
 */
function extractCodeFromEmail(email) {
    const content = `${email.subject || ''} ${email.body || ''} ${email.html_body || ''}`;

    // Pattern 1: XXX-XXX format (e.g., OMK-QZN)
    const pattern1 = /\b([A-Z0-9]{3}-[A-Z0-9]{3})\b/i;
    const match1 = content.match(pattern1);
    if (match1) {
        return match1[1].replace('-', ''); // Remove dash to get XXXXXX
    }

    // Pattern 2: 6-digit alphanumeric code
    const pattern2 = /\b([A-Z0-9]{6})\b/i;
    const match2 = content.match(pattern2);
    if (match2) {
        return match2[1];
    }

    // Pattern 3: "code: XXXXXX" or "code is XXXXXX"
    const pattern3 = /code[:\s]+([A-Z0-9]{6})/i;
    const match3 = content.match(pattern3);
    if (match3) {
        return match3[1];
    }

    // Pattern 4: "verification code" followed by code
    const pattern4 = /verification\s+code[:\s]+([A-Z0-9]{6})/i;
    const match4 = content.match(pattern4);
    if (match4) {
        return match4[1];
    }

    return null;
}

/**
 * Sleep helper function
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise<void>}
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = {
    generateEmail,
    checkEmailForCode
};
