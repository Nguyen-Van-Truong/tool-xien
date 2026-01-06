/**
 * Random Verify Generator
 * Based on ThanhNguyxn/SheerID-Verification-Tool
 * 
 * This module contains functions to generate random veteran data,
 * device fingerprints, and NewRelic tracking headers.
 */

const RandomVerifyGenerator = {
    // Common American first names
    FIRST_NAMES: [
        'James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph',
        'Thomas', 'Charles', 'Christopher', 'Daniel', 'Matthew', 'Anthony', 'Mark',
        'Donald', 'Steven', 'Paul', 'Andrew', 'Joshua', 'Kenneth', 'Kevin', 'Brian',
        'George', 'Timothy', 'Ronald', 'Edward', 'Jason', 'Jeffrey', 'Ryan',
        'Jacob', 'Nicholas', 'Gary', 'Eric', 'Jonathan', 'Stephen', 'Larry', 'Justin',
        'Scott', 'Brandon', 'Benjamin', 'Samuel', 'Raymond', 'Gregory', 'Frank'
    ],

    // Common American last names
    LAST_NAMES: [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
        'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
        'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
        'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson',
        'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen',
        'Hill', 'Flores', 'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera'
    ],

    /**
     * Generate random name
     * @returns {Object} { firstName, lastName, fullName }
     */
    generateName() {
        const firstName = this.FIRST_NAMES[Math.floor(Math.random() * this.FIRST_NAMES.length)];
        const lastName = this.LAST_NAMES[Math.floor(Math.random() * this.LAST_NAMES.length)];
        return {
            firstName,
            lastName,
            fullName: `${firstName} ${lastName}`
        };
    },

    /**
     * Generate random email address
     * @param {string} domain - Email domain (default: gmail.com)
     * @returns {string} Random email
     */
    generateEmail(domain = 'gmail.com') {
        const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
        let username = '';
        for (let i = 0; i < 10; i++) {
            username += chars[Math.floor(Math.random() * chars.length)];
        }
        return `${username}@${domain}`;
    },

    /**
     * Generate random birth date for veteran (age 25-55)
     * @param {number} minAge - Minimum age (default: 25)
     * @param {number} maxAge - Maximum age (default: 55)
     * @returns {string} Birth date in YYYY-MM-DD format
     */
    generateBirthDate(minAge = 25, maxAge = 55) {
        const today = new Date();
        const minDate = new Date(today);
        minDate.setFullYear(today.getFullYear() - maxAge);

        const maxDate = new Date(today);
        maxDate.setFullYear(today.getFullYear() - minAge);

        const randomTime = minDate.getTime() + Math.random() * (maxDate.getTime() - minDate.getTime());
        const birthDate = new Date(randomTime);

        const year = birthDate.getFullYear();
        const month = String(birthDate.getMonth() + 1).padStart(2, '0');
        const day = String(birthDate.getDate()).padStart(2, '0');

        return `${year}-${month}-${day}`;
    },

    /**
     * Generate random discharge date (optimized for SheerID auto-approval)
     * SheerID targets veterans discharged within 12 months
     * @param {number} minDays - Minimum days ago (default: 30)
     * @param {number} maxDays - Maximum days ago (default: 330)
     * @returns {string} Discharge date in YYYY-MM-DD format
     */
    generateDischargeDate(minDays = 30, maxDays = 330) {
        const today = new Date();
        const randomDays = Math.floor(Math.random() * (maxDays - minDays + 1)) + minDays;
        const dischargeDate = new Date(today);
        dischargeDate.setDate(today.getDate() - randomDays);

        const year = dischargeDate.getFullYear();
        const month = String(dischargeDate.getMonth() + 1).padStart(2, '0');
        const day = String(dischargeDate.getDate()).padStart(2, '0');

        return `${year}-${month}-${day}`;
    },

    /**
     * Get random military branch from main branches
     * @param {Array} branches - Array of branch names
     * @returns {string} Random branch name
     */
    getRandomBranch(branches = ['Army', 'Air Force', 'Navy', 'Marine Corps', 'Coast Guard']) {
        return branches[Math.floor(Math.random() * branches.length)];
    },

    /**
     * Generate device fingerprint (MD5-like hash)
     * @param {Array} screens - Array of screen resolutions
     * @returns {string} 32-character hex fingerprint
     */
    generateFingerprint(screens = ['1920x1080', '2560x1440', '1366x768', '1440x900', '1536x864']) {
        const screen = screens[Math.floor(Math.random() * screens.length)];
        const timestamp = Date.now();
        const uuid = this._generateUUID();
        const raw = `${screen}|${timestamp}|${uuid}`;

        // Simple hash function (mimics MD5 output format)
        return this._simpleHash(raw);
    },

    /**
     * Generate NewRelic tracking headers
     * @param {string} accountId - NewRelic account ID
     * @param {string} appId - NewRelic app ID
     * @returns {Object} { newrelic, traceparent, tracestate }
     */
    generateNewRelicHeaders(accountId = '364029', appId = '134291347') {
        const traceId = this._generateHexString(32);
        const spanId = this._generateHexString(16);
        const timestamp = Date.now();

        const payload = {
            v: [0, 1],
            d: {
                ty: 'Browser',
                ac: accountId,
                ap: appId,
                id: spanId,
                tr: traceId,
                ti: timestamp
            }
        };

        // Base64 encode the payload
        const newrelicHeader = btoa(JSON.stringify(payload));

        return {
            newrelic: newrelicHeader,
            traceparent: `00-${traceId}-${spanId}-01`,
            tracestate: `${accountId}@nr=0-1-${accountId}-${appId}-${spanId}----${timestamp}`
        };
    },

    /**
     * Generate complete random veteran data
     * @param {Object} config - Configuration object
     * @returns {Object} Complete veteran data for verification
     */
    generateVeteranData(config = {}) {
        const name = this.generateName();
        const branch = config.branch || this.getRandomBranch(config.branches);

        return {
            firstName: name.firstName,
            lastName: name.lastName,
            fullName: name.fullName,
            branch: branch,
            birthDate: this.generateBirthDate(config.minAge || 25, config.maxAge || 55),
            dischargeDate: this.generateDischargeDate(config.minDischargeDays || 30, config.maxDischargeDays || 330),
            email: config.email || this.generateEmail(),
            fingerprint: this.generateFingerprint(config.screens),
            newRelicHeaders: this.generateNewRelicHeaders(config.accountId, config.appId)
        };
    },

    // === Private Helper Functions ===

    /**
     * Generate UUID v4
     * @private
     */
    _generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    },

    /**
     * Generate random hex string
     * @private
     */
    _generateHexString(length) {
        const chars = '0123456789abcdef';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars[Math.floor(Math.random() * chars.length)];
        }
        return result;
    },

    /**
     * Simple hash function (produces MD5-like output)
     * @private
     */
    _simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }

        // Convert to 32-char hex string
        const hexHash = Math.abs(hash).toString(16).padStart(8, '0');
        const timestamp = Date.now().toString(16).padStart(12, '0');
        const random = this._generateHexString(12);

        return (hexHash + timestamp + random).substring(0, 32);
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RandomVerifyGenerator;
}
