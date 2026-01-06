/**
 * Random Verify API Handler
 * Based on ThanhNguyxn/SheerID-Verification-Tool
 * 
 * This module handles SheerID API calls with enhanced headers.
 * It uses RandomVerifyConfig and RandomVerifyGenerator.
 */

const RandomVerifyAPI = {
    /**
     * Parse verificationId from URL
     * @param {string} url - SheerID URL
     * @returns {string|null} Verification ID or null
     */
    parseVerificationId(url) {
        if (!url) return null;

        // Priority 1: Match verificationId parameter
        let match = url.match(/verificationId=([a-f0-9]+)/i);
        if (match) return match[1];

        // Priority 2: Match verify/xxx path (but not program ID which is shorter)
        match = url.match(/verify\/([a-f0-9]{24,})(?:\?|$)/i);
        if (match) return match[1];

        return null;
    },

    /**
     * Build headers for SheerID API request
     * @param {Object} newRelicHeaders - Generated NewRelic headers
     * @returns {Object} Complete headers object
     */
    buildHeaders(newRelicHeaders) {
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'sec-ch-ua': '"Chromium";v="131", "Google Chrome";v="131"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'User-Agent': RandomVerifyConfig.USER_AGENT,
            'Accept-Language': 'en-US,en;q=0.9',
            'clientversion': RandomVerifyConfig.CLIENT_VERSION,
            'clientname': RandomVerifyConfig.CLIENT_NAME,
            'newrelic': newRelicHeaders.newrelic,
            'traceparent': newRelicHeaders.traceparent,
            'tracestate': newRelicHeaders.tracestate,
            'Origin': RandomVerifyConfig.SHEERID_BASE_URL
        };
    },

    /**
     * Build metadata for Step 2 payload
     * @param {string} verificationId - Verification ID
     * @returns {Object} Metadata object
     */
    buildMetadata(verificationId) {
        const refererUrl = `${RandomVerifyConfig.SHEERID_BASE_URL}/verify/${RandomVerifyConfig.PROGRAM_ID}/?verificationId=${verificationId}`;

        return {
            marketConsentValue: false,
            refererUrl: refererUrl,
            verificationId: verificationId,
            flags: JSON.stringify({
                'doc-upload-considerations': 'default',
                'doc-upload-may24': 'default',
                'doc-upload-redesign-use-legacy-message-keys': false,
                'docUpload-assertion-checklist': 'default',
                'include-cvec-field-france-student': 'not-labeled-optional',
                'org-search-overlay': 'default',
                'org-selected-display': 'default'
            }),
            submissionOptIn: 'By submitting the personal information above, I acknowledge that my personal information is being collected under the privacy policy of the business from which I am seeking a discount, and I understand that my personal information will be shared with SheerID as a processor/third-party service provider in order for SheerID to confirm my eligibility for a special offer.'
        };
    },

    /**
     * Execute Step 1: collectMilitaryStatus
     * @param {string} verificationId - Verification ID
     * @param {Object} headers - Request headers
     * @param {string} status - Military status (default: VETERAN)
     * @returns {Promise<Object>} Response data and status code
     */
    async step1CollectMilitaryStatus(verificationId, headers, status = 'VETERAN') {
        const url = `${RandomVerifyConfig.SHEERID_API}/verification/${verificationId}/step/collectMilitaryStatus`;

        console.log('🔶 [RandomVerify] Step 1: collectMilitaryStatus');
        console.log('   URL:', url);
        console.log('   Status:', status);

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ status: status })
            });

            const statusCode = response.status;
            console.log('   Response:', statusCode);

            if (!response.ok) {
                const errorText = await response.text();
                return {
                    success: false,
                    statusCode,
                    error: errorText,
                    isRateLimit: statusCode === 429 || errorText.includes('verificationLimitExceeded')
                };
            }

            const data = await response.json();
            console.log('   currentStep:', data.currentStep);

            return {
                success: true,
                statusCode,
                data,
                currentStep: data.currentStep,
                submissionUrl: data.submissionUrl
            };
        } catch (error) {
            console.error('   Error:', error);
            return { success: false, error: error.message };
        }
    },

    /**
     * Execute Step 2: collectInactiveMilitaryPersonalInfo
     * @param {string} verificationId - Verification ID
     * @param {string} submissionUrl - URL from Step 1 or default
     * @param {Object} veteranData - Veteran data to submit
     * @param {Object} headers - Request headers
     * @returns {Promise<Object>} Response data and status code
     */
    async step2CollectPersonalInfo(verificationId, submissionUrl, veteranData, headers) {
        const url = submissionUrl ||
            `${RandomVerifyConfig.SHEERID_API}/verification/${verificationId}/step/collectInactiveMilitaryPersonalInfo`;

        // Get organization from branch
        const org = RandomVerifyConfig.BRANCH_ORG_MAP[veteranData.branch] ||
            RandomVerifyConfig.BRANCH_ORG_MAP['Army'];

        const payload = {
            firstName: veteranData.firstName,
            lastName: veteranData.lastName,
            birthDate: veteranData.birthDate,
            email: veteranData.email,
            phoneNumber: '',
            organization: {
                id: org.id,
                name: org.name
            },
            dischargeDate: veteranData.dischargeDate,
            deviceFingerprintHash: veteranData.fingerprint,
            locale: 'en-US',
            country: 'US',
            metadata: this.buildMetadata(verificationId)
        };

        console.log('🔶 [RandomVerify] Step 2: collectInactiveMilitaryPersonalInfo');
        console.log('   URL:', url);
        console.log('   Veteran:', veteranData.firstName, veteranData.lastName);
        console.log('   Branch:', org.name);
        console.log('   Birth:', veteranData.birthDate);
        console.log('   Discharge:', veteranData.dischargeDate);
        console.log('   Email:', veteranData.email);

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(payload)
            });

            const statusCode = response.status;
            console.log('   Response:', statusCode);

            if (!response.ok) {
                const errorText = await response.text();
                return {
                    success: false,
                    statusCode,
                    error: errorText,
                    isRateLimit: statusCode === 429 || errorText.includes('verificationLimitExceeded')
                };
            }

            const data = await response.json();
            console.log('   currentStep:', data.currentStep);

            return {
                success: true,
                statusCode,
                data,
                currentStep: data.currentStep,
                redirectUrl: data.redirectUrl,
                rewardCode: data.rewardCode
            };
        } catch (error) {
            console.error('   Error:', error);
            return { success: false, error: error.message };
        }
    },

    /**
     * Main verification function - executes complete flow
     * @param {string} verificationId - Verification ID
     * @param {string} email - Email to use (optional, will generate if empty)
     * @returns {Promise<Object>} Verification result
     */
    async verify(verificationId, email = null) {
        console.log('🚀 [RandomVerify] Starting verification...');
        console.log('   verificationId:', verificationId);

        // Generate random veteran data
        const veteranData = RandomVerifyGenerator.generateVeteranData({
            email: email,
            branches: RandomVerifyConfig.MAIN_BRANCHES,
            minAge: RandomVerifyConfig.MIN_AGE,
            maxAge: RandomVerifyConfig.MAX_AGE,
            minDischargeDays: RandomVerifyConfig.MIN_DISCHARGE_DAYS,
            maxDischargeDays: RandomVerifyConfig.MAX_DISCHARGE_DAYS,
            screens: RandomVerifyConfig.SCREEN_RESOLUTIONS,
            accountId: RandomVerifyConfig.NEWRELIC.accountId,
            appId: RandomVerifyConfig.NEWRELIC.appId
        });

        console.log('🎲 Generated veteran:', veteranData.fullName);
        console.log('   Branch:', veteranData.branch);
        console.log('   Birth:', veteranData.birthDate);
        console.log('   Discharge:', veteranData.dischargeDate);
        console.log('   Email:', veteranData.email);

        // Build headers
        const headers = this.buildHeaders(veteranData.newRelicHeaders);

        // Step 1
        const step1Result = await this.step1CollectMilitaryStatus(verificationId, headers);

        if (!step1Result.success) {
            return {
                success: false,
                step: 1,
                error: step1Result.error,
                isRateLimit: step1Result.isRateLimit,
                veteranData: veteranData
            };
        }

        // Check if already at success/emailLoop
        if (step1Result.currentStep === 'success' || step1Result.currentStep === 'emailLoop') {
            return {
                success: true,
                currentStep: step1Result.currentStep,
                data: step1Result.data,
                veteranData: veteranData
            };
        }

        // Check if unexpected step
        if (step1Result.currentStep !== 'collectInactiveMilitaryPersonalInfo') {
            return {
                success: false,
                step: 1,
                error: `Unexpected step: ${step1Result.currentStep}`,
                currentStep: step1Result.currentStep,
                veteranData: veteranData
            };
        }

        // Step 2
        const step2Result = await this.step2CollectPersonalInfo(
            verificationId,
            step1Result.submissionUrl,
            veteranData,
            headers
        );

        if (!step2Result.success) {
            return {
                success: false,
                step: 2,
                error: step2Result.error,
                isRateLimit: step2Result.isRateLimit,
                veteranData: veteranData
            };
        }

        // Build result
        const result = {
            success: step2Result.currentStep !== 'error',
            currentStep: step2Result.currentStep,
            data: step2Result.data,
            veteranData: veteranData,
            redirectUrl: step2Result.redirectUrl,
            rewardCode: step2Result.rewardCode
        };

        // Add status-specific info
        if (step2Result.currentStep === 'success') {
            result.message = '🎉 Verification successful!';
            result.pending = false;
        } else if (step2Result.currentStep === 'emailLoop') {
            result.message = '📧 Email verification required - check inbox';
            result.pending = true;
        } else if (step2Result.currentStep === 'docUpload') {
            result.success = false;
            result.message = '📄 Document upload required - auto verification failed';
            result.pending = true;
        } else {
            result.message = `Status: ${step2Result.currentStep}`;
            result.pending = true;
        }

        console.log('✅ [RandomVerify] Complete:', result.message);

        return result;
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RandomVerifyAPI;
}
