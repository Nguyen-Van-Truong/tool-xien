/**
 * Payment Link Converter
 * Chuyển đổi link từ chatgpt.com/checkout sang pay.openai.com
 */

// Constants
const PAY_BASE_URL = 'https://pay.openai.com/c/pay/';
const CHECKOUT_SUFFIX = '#fidnandhYHdWcXxpYCc%2FJ2FgY2RwaXEnKSdpamZkaWAnPydgaycpJ3ZwZ3Zmd2x1cWxqa1BrbHRwYGtgdnZAa2RnaWBhJz9jZGl2YCknZHVsTmB8Jz8ndW5aaWxzYFowNE1Kd1ZyRjNtNGt9QmpMNmlRRGJXb1xTd38xYVA2Y1NKZGd8RmZOVzZ1Z0BPYnBGU0RpdEZ9YX1GUHNqV200XVJyV2RmU2xqc1A2bklOc3Vub20yTHRuUjU1bF1Udm9qNmsnKSdjd2poVmB3c2B3Jz9xd3BgKSdnZGZuYW5qcGthRmppancnPycmY2NjY2NjJyknaWR8anBxUXx1YCc%2FJ3Zsa2JpYFpscWBoJyknYGtkZ2lgVWlkZmBtamlhYHd2Jz9xd3BgeCUl';

/**
 * Extract token từ URL hoặc input string
 * @param {string} input - URL hoặc token
 * @returns {string|null} - Token hoặc null nếu không tìm thấy
 */
function extractToken(input) {
  if (!input || typeof input !== 'string') {
    return null;
  }

  input = input.trim();

  // Nếu input đã là token hợp lệ, return luôn
  if (/^cs_live_[a-zA-Z0-9]+$/.test(input)) {
    return input;
  }

  // Nếu là URL, extract token
  const match = input.match(/cs_live_[a-zA-Z0-9]+/);
  return match ? match[0] : null;
}

/**
 * Validate token
 * @param {string} token - Token cần validate
 * @returns {boolean} - true nếu token hợp lệ
 */
function validateToken(token) {
  if (!token || typeof token !== 'string') {
    return false;
  }
  return /^cs_live_[a-zA-Z0-9]+$/.test(token);
}

/**
 * Chuyển đổi token thành pay.openai.com URL
 * @param {string} token - Token cs_live_xxx
 * @returns {string} - URL pay.openai.com đầy đủ
 */
function convertTokenToPayURL(token) {
  if (!validateToken(token)) {
    throw new Error('Token không hợp lệ. Token phải bắt đầu bằng cs_live_');
  }
  return `${PAY_BASE_URL}${token}${CHECKOUT_SUFFIX}`;
}

/**
 * Chuyển đổi checkout link sang pay link (hàm main)
 * @param {string} input - URL checkout hoặc token
 * @returns {object} - { success: boolean, url?: string, error?: string }
 */
function convertCheckoutLink(input) {
  try {
    // Extract token
    const token = extractToken(input);
    
    if (!token) {
      return {
        success: false,
        error: 'Không tìm thấy token cs_live_ trong input'
      };
    }

    // Validate token
    if (!validateToken(token)) {
      return {
        success: false,
        error: 'Token không hợp lệ. Token phải bắt đầu bằng cs_live_ và chỉ chứa chữ cái và số'
      };
    }

    // Convert to pay URL
    const url = convertTokenToPayURL(token);

    return {
      success: true,
      url: url,
      token: token
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// Export cho Node.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    convertCheckoutLink,
    extractToken,
    validateToken,
    convertTokenToPayURL,
    PAY_BASE_URL,
    CHECKOUT_SUFFIX
  };
}

// Export cho browser
if (typeof window !== 'undefined') {
  window.PaymentLinkConverter = {
    convertCheckoutLink,
    extractToken,
    validateToken,
    convertTokenToPayURL,
    PAY_BASE_URL,
    CHECKOUT_SUFFIX
  };
}
