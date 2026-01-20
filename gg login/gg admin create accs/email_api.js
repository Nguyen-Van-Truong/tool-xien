/**
 * Email API - Tinyhost.shop Integration
 * Dùng để tạo email tạm và check inbox lấy link verification
 */

const fetch = require('node-fetch');

const EmailAPI = {
    BASE_URL: 'https://tinyhost.shop/api',
    logCallback: null,

    // Set log callback để gửi log lên UI
    setLogCallback(callback) {
        this.logCallback = callback;
    },

    log(message) {
        console.log(message);
        if (this.logCallback) {
            this.logCallback(message);
        }
    },

    /**
     * Lấy danh sách domain ngẫu nhiên
     */
    async getRandomDomains(limit = 10) {
        try {
            const response = await fetch(`${this.BASE_URL}/random-domains/?limit=${limit}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch domains: ${response.status}`);
            }
            const data = await response.json();
            return data.domains || [];
        } catch (error) {
            this.log(`❌ Error fetching domains: ${error.message}`);
            return [];
        }
    },

    /**
     * Tạo email ngẫu nhiên
     */
    async generateEmail() {
        try {
            const domains = await this.getRandomDomains(10);
            if (domains.length === 0) {
                throw new Error('No domains available');
            }

            const randomDomain = domains[Math.floor(Math.random() * domains.length)];

            const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
            let username = '';
            for (let i = 0; i < 16; i++) {
                username += chars.charAt(Math.floor(Math.random() * chars.length));
            }

            return `${username}@${randomDomain}`;
        } catch (error) {
            this.log(`❌ Error generating email: ${error.message}`);
            return null;
        }
    },

    /**
     * Check inbox và tìm link verification
     * @param {string} email - Email cần check
     * @param {number} maxAttempts - Số lần thử tối đa (giảm xuống 8)
     * @param {number} delayMs - Delay giữa các lần thử (ms)
     */
    async checkInboxForLink(email, maxAttempts = 8, delayMs = 2000) {
        const [username, domain] = email.split('@');
        if (!username || !domain) {
            this.log('❌ Invalid email format');
            return null;
        }

        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                this.log(`   📬 Check inbox (${attempt}/${maxAttempts}): ${email}`);

                const response = await fetch(`${this.BASE_URL}/email/${domain}/${username}/?page=1&limit=20`);
                if (!response.ok) {
                    this.log(`   ⚠️ API error: ${response.status}`);
                    await this.delay(delayMs);
                    continue;
                }

                const data = await response.json();
                const emails = data.emails || [];

                if (emails.length === 0) {
                    this.log(`   📭 No emails yet (${attempt}/${maxAttempts})...`);
                    await this.delay(delayMs);
                    continue;
                }

                this.log(`   📨 Found ${emails.length} email(s), scanning...`);

                // Sort by date (newest first)
                emails.sort((a, b) => new Date(b.date) - new Date(a.date));

                // Tìm link Google trong email
                for (const mail of emails) {
                    if (mail.html_body) {
                        let match = mail.html_body.match(/https:\/\/accounts\.google\.com\/[^"'\s<>]+/i);
                        if (match) {
                            const link = match[0].replace(/&amp;/g, '&');
                            this.log('   ✅ Found Google link!');
                            return link;
                        }
                    }

                    if (mail.body) {
                        let match = mail.body.match(/https:\/\/accounts\.google\.com\/[^"'\s<>()]+/i);
                        if (match) {
                            const link = match[0].replace(/&amp;/g, '&');
                            this.log('   ✅ Found Google link!');
                            return link;
                        }
                    }
                }

                this.log('   📭 No verification link in emails yet...');
                await this.delay(delayMs);

            } catch (error) {
                this.log(`   ⚠️ Check error: ${error.message}`);
                await this.delay(delayMs);
            }
        }

        this.log(`   ❌ Timeout - không tìm thấy link sau ${maxAttempts} lần`);
        return null;
    },

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
};

module.exports = EmailAPI;

