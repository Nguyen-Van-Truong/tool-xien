/**
 * Random Verify Configuration
 * Based on ThanhNguyxn/SheerID-Verification-Tool
 * 
 * This module contains all configuration constants for the Random Verify feature.
 */

const RandomVerifyConfig = {
    // SheerID API Configuration
    SHEERID_BASE_URL: 'https://services.sheerid.com',
    SHEERID_API: 'https://services.sheerid.com/rest/v2',

    // ChatGPT Veterans Program ID
    PROGRAM_ID: '690415d58971e73ca187d8c9',

    // Military Status Options
    MILITARY_STATUS: ['VETERAN', 'ACTIVE_DUTY', 'RESERVIST'],
    DEFAULT_STATUS: 'VETERAN',

    // User Agent (Chrome on Windows)
    USER_AGENT: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',

    // Military Branch Organization IDs
    BRANCH_ORG_MAP: {
        'Army': { id: 4070, name: 'Army' },
        'Air Force': { id: 4073, name: 'Air Force' },
        'Navy': { id: 4072, name: 'Navy' },
        'Marine Corps': { id: 4071, name: 'Marine Corps' },
        'Coast Guard': { id: 4074, name: 'Coast Guard' },
        'Space Force': { id: 4544268, name: 'Space Force' },
        'Army National Guard': { id: 4075, name: 'Army National Guard' },
        'Army Reserve': { id: 4076, name: 'Army Reserve' },
        'Air National Guard': { id: 4079, name: 'Air National Guard' },
        'Air Force Reserve': { id: 4080, name: 'Air Force Reserve' },
        'Navy Reserve': { id: 4078, name: 'Navy Reserve' },
        'Marine Corps Reserve': { id: 4077, name: 'Marine Corps Forces Reserve' },
        'Coast Guard Reserve': { id: 4081, name: 'Coast Guard Reserve' }
    },

    // Main branches for random selection (higher success rate)
    MAIN_BRANCHES: ['Army', 'Air Force', 'Navy', 'Marine Corps', 'Coast Guard'],

    // Age range for random birth date
    MIN_AGE: 25,
    MAX_AGE: 55,

    // Discharge date range (days ago) - optimized for SheerID auto-approval
    // SheerID targets veterans discharged within 12 months
    MIN_DISCHARGE_DAYS: 30,   // At least 1 month ago
    MAX_DISCHARGE_DAYS: 330,  // Less than 11 months ago

    // Screen resolutions for fingerprint
    SCREEN_RESOLUTIONS: ['1920x1080', '2560x1440', '1366x768', '1440x900', '1536x864'],

    // NewRelic tracking config
    NEWRELIC: {
        accountId: '364029',
        appId: '134291347'
    },

    // Client version (from SheerID JS library)
    CLIENT_VERSION: '2.157.0',
    CLIENT_NAME: 'jslib'
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RandomVerifyConfig;
}
