/**
 * Account Generator
 * Auto-generates random account data for testing
 */

// Random name lists
const firstNames = [
    'John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma', 'James', 'Emily',
    'Robert', 'Olivia', 'William', 'Sophia', 'Daniel', 'Isabella', 'Thomas',
    'Mia', 'Christopher', 'Charlotte', 'Matthew', 'Amelia', 'Andrew', 'Harper'
];

const lastNames = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
    'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
    'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'
];

const emailDomains = [
    'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'protonmail.com',
    'icloud.com', 'aol.com', 'mail.com', 'zoho.com', 'gmx.com'
];

/**
 * Generate random string
 */
function randomString(length) {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

/**
 * Generate random password (meets requirements)
 */
function generatePassword() {
    const upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const lower = 'abcdefghijklmnopqrstuvwxyz';
    const digits = '0123456789';
    const special = '!@#$%^&*';

    // Ensure at least 1 of each type
    let password = '';
    password += upper.charAt(Math.floor(Math.random() * upper.length));
    password += lower.charAt(Math.floor(Math.random() * lower.length));
    password += digits.charAt(Math.floor(Math.random() * digits.length));
    password += special.charAt(Math.floor(Math.random() * special.length));

    // Fill rest with random chars
    const allChars = upper + lower + digits + special;
    for (let i = 4; i < 12; i++) {
        password += allChars.charAt(Math.floor(Math.random() * allChars.length));
    }

    // Shuffle password
    return password.split('').sort(() => Math.random() - 0.5).join('');
}

/**
 * Generate single account
 */
function generateAccount() {
    const firstName = firstNames[Math.floor(Math.random() * firstNames.length)];
    const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
    const domain = emailDomains[Math.floor(Math.random() * emailDomains.length)];

    const username = `${firstName.toLowerCase()}.${lastName.toLowerCase()}.${randomString(4)}`;
    const email = `${username}@${domain}`;
    const password = generatePassword();

    return {
        email,
        password,
        firstname: firstName,
        lastname: lastName
    };
}

/**
 * Generate multiple accounts
 */
function generateAccounts(count = 5) {
    const accounts = [];
    for (let i = 0; i < count; i++) {
        accounts.push(generateAccount());
    }
    return accounts;
}

/**
 * Format accounts for input (email|password|firstname|lastname)
 */
function formatForInput(accounts) {
    return accounts.map(acc =>
        `${acc.email}|${acc.password}|${acc.firstname}|${acc.lastname}`
    ).join('\n');
}

// CLI usage
if (require.main === module) {
    const count = parseInt(process.argv[2]) || 5;
    const accounts = generateAccounts(count);

    console.log(`\n📝 Generated ${count} test accounts:\n`);
    console.log(formatForInput(accounts));
    console.log('\n✅ Copy above and paste into GUI, or use test_cli.js\n');
}

module.exports = {
    generateAccount,
    generateAccounts,
    formatForInput
};
