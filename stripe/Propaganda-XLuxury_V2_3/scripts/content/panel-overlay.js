// Propaganda Panel Overlay - NEURO//PAY Style UI
// Injects floating control panel on Stripe checkout pages

(function () {
    'use strict';

    // State
    let panelState = {
        history: 0,
        aiSolver: true,
        minimized: false,
        cardProtocol: 'mastercard',
        region: 'US',
        customBin: '',
        expiry: '',
        cvv: ''
    };

    // Load state from storage
    function loadState() {
        try {
            chrome.storage.local.get(['panelState'], (result) => {
                if (result.panelState) {
                    panelState = { ...panelState, ...result.panelState };
                    updatePanelUI();
                }
            });
        } catch (e) {
            console.log('Panel: Using default state');
        }
    }

    // Save state to storage
    function saveState() {
        try {
            chrome.storage.local.set({ panelState });
        } catch (e) {
            console.log('Panel: Could not save state');
        }
    }

    // Create Panel HTML
    function createPanel() {
        const panel = document.createElement('div');
        panel.className = 'propaganda-panel';
        panel.id = 'propaganda-panel';

        panel.innerHTML = `
      <div class="panel-header">
        <div class="panel-logo">
          <span class="panel-logo-icon">⚡</span>
          <span class="panel-title">NEURO<span>//PAY</span></span>
          <span class="panel-badge">+ STRIPE</span>
        </div>
        <div class="panel-controls">
          <button class="panel-btn-icon" id="btn-settings" title="Settings">⚙</button>
          <button class="panel-btn-icon" id="btn-minimize" title="Minimize">−</button>
        </div>
      </div>
      
      <div class="panel-content">
        <div class="panel-actions">
          <button class="btn-action" id="btn-generate">GENERATE</button>
          <button class="btn-action" id="btn-import">+ IMPORT</button>
          <button class="btn-action" id="btn-verify">+ VERIFY</button>
        </div>
        
        <div class="section-label">CARD PROTOCOL</div>
        <select class="panel-select" id="card-protocol">
          <option value="mastercard">+ MASTERCARD</option>
          <option value="visa">+ VISA</option>
          <option value="amex">+ AMEX</option>
          <option value="discover">+ DISCOVER</option>
        </select>
        
        <div class="config-section">
          <div class="config-toggle">
            <span class="config-toggle-label">◇ ADVANCED CONFIG</span>
            <span class="config-toggle-dot"></span>
          </div>
          
          <div class="section-label">CUSTOM BIN</div>
          <input type="text" class="panel-input" id="custom-bin" placeholder="••••••••••••••••" maxlength="16">
          <div style="font-size:9px;color:rgba(255,255,255,0.3);margin-top:-8px;margin-bottom:8px;">6-8 DIGITS (AUTO EMPTY)</div>
          
          <div class="input-row">
            <div style="flex:1">
              <div class="section-label">EXPIRY</div>
              <input type="text" class="panel-input" id="expiry" placeholder="••/••" maxlength="5">
            </div>
            <div style="flex:1">
              <div class="section-label">CVV</div>
              <input type="text" class="panel-input" id="cvv" placeholder="•••" maxlength="4">
            </div>
          </div>
        </div>
        
        <div class="region-section">
          <div class="section-label">REGION</div>
          <select class="panel-select" id="region">
            <option value="US">( US ) UNITED STATES</option>
            <option value="UK">( UK ) UNITED KINGDOM</option>
            <option value="CA">( CA ) CANADA</option>
            <option value="AU">( AU ) AUSTRALIA</option>
            <option value="DE">( DE ) GERMANY</option>
            <option value="FR">( FR ) FRANCE</option>
            <option value="IT">( IT ) ITALY</option>
            <option value="ES">( ES ) SPAIN</option>
            <option value="NL">( NL ) NETHERLANDS</option>
            <option value="JP">( JP ) JAPAN</option>
          </select>
        </div>
        
        <div class="stats-row">
          <div class="stat-box">
            <div class="stat-label">◇ HISTORY</div>
            <div class="stat-value" id="history-count">0</div>
          </div>
          <div class="toggle-box">
            <div class="toggle-label">AI SOLVER</div>
            <div class="toggle-switch active" id="ai-solver"></div>
          </div>
        </div>
        
        <button class="btn-main" id="btn-generate-fill">GENERATE & FILL</button>
        <div class="keybind-hint">(CTRL+SHIFT+F)</div>
        
        <div class="utility-buttons">
          <button class="btn-utility export" id="btn-export">+ EXPORT</button>
          <button class="btn-utility sync" id="btn-sync">+ SYNC</button>
          <button class="btn-utility clear" id="btn-clear">+ CLEAR</button>
        </div>
        
        <div class="panel-footer">
          <div class="footer-text">NEURO//PAY v3.1 (CYBERPUNK EDITION)</div>
        </div>
      </div>
    `;

        return panel;
    }

    // Make panel draggable
    function makeDraggable(element) {
        let isDragging = false;
        let startX, startY, startLeft, startTop;

        element.addEventListener('mousedown', (e) => {
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'SELECT' || e.target.tagName === 'INPUT') {
                return;
            }

            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;

            const rect = element.getBoundingClientRect();
            startLeft = rect.left;
            startTop = rect.top;

            element.style.cursor = 'grabbing';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;

            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;

            element.style.left = (startLeft + deltaX) + 'px';
            element.style.top = (startTop + deltaY) + 'px';
            element.style.right = 'auto';
        });

        document.addEventListener('mouseup', () => {
            isDragging = false;
            element.style.cursor = 'move';
        });
    }

    // Update panel UI from state
    function updatePanelUI() {
        const panel = document.getElementById('propaganda-panel');
        if (!panel) return;

        const historyCount = panel.querySelector('#history-count');
        const aiSolver = panel.querySelector('#ai-solver');
        const cardProtocol = panel.querySelector('#card-protocol');
        const region = panel.querySelector('#region');
        const customBin = panel.querySelector('#custom-bin');
        const expiry = panel.querySelector('#expiry');
        const cvv = panel.querySelector('#cvv');

        if (historyCount) historyCount.textContent = panelState.history;
        if (aiSolver) aiSolver.classList.toggle('active', panelState.aiSolver);
        if (cardProtocol) cardProtocol.value = panelState.cardProtocol;
        if (region) region.value = panelState.region;
        if (customBin) customBin.value = panelState.customBin;
        if (expiry) expiry.value = panelState.expiry;
        if (cvv) cvv.value = panelState.cvv;

        if (panelState.minimized) {
            panel.classList.add('minimized');
        }
    }

    // Bind events
    function bindEvents(panel) {
        // Minimize button
        const btnMinimize = panel.querySelector('#btn-minimize');
        btnMinimize?.addEventListener('click', () => {
            panel.classList.toggle('minimized');
            panelState.minimized = panel.classList.contains('minimized');
            btnMinimize.textContent = panelState.minimized ? '+' : '−';
            saveState();
        });

        // Settings button
        const btnSettings = panel.querySelector('#btn-settings');
        btnSettings?.addEventListener('click', () => {
            chrome.runtime.sendMessage({ action: 'openSettings' });
        });

        // Generate button
        const btnGenerate = panel.querySelector('#btn-generate');
        btnGenerate?.addEventListener('click', () => {
            generateCard();
            btnGenerate.classList.add('active');
            setTimeout(() => btnGenerate.classList.remove('active'), 200);
        });

        // Import button
        const btnImport = panel.querySelector('#btn-import');
        btnImport?.addEventListener('click', () => {
            alert('Import cards from CC list in Settings');
        });

        // Verify button
        const btnVerify = panel.querySelector('#btn-verify');
        btnVerify?.addEventListener('click', () => {
            alert('Card verification triggered');
        });

        // Card Protocol
        const cardProtocol = panel.querySelector('#card-protocol');
        cardProtocol?.addEventListener('change', (e) => {
            panelState.cardProtocol = e.target.value;
            saveState();
        });

        // Region
        const region = panel.querySelector('#region');
        region?.addEventListener('change', (e) => {
            panelState.region = e.target.value;
            saveState();
        });

        // Custom BIN
        const customBin = panel.querySelector('#custom-bin');
        customBin?.addEventListener('input', (e) => {
            panelState.customBin = e.target.value.replace(/\D/g, '');
            e.target.value = panelState.customBin;
            saveState();
        });

        // Expiry
        const expiry = panel.querySelector('#expiry');
        expiry?.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.slice(0, 2) + '/' + value.slice(2, 4);
            }
            e.target.value = value;
            panelState.expiry = value;
            saveState();
        });

        // CVV
        const cvv = panel.querySelector('#cvv');
        cvv?.addEventListener('input', (e) => {
            panelState.cvv = e.target.value.replace(/\D/g, '');
            e.target.value = panelState.cvv;
            saveState();
        });

        // AI Solver toggle
        const aiSolver = panel.querySelector('#ai-solver');
        aiSolver?.addEventListener('click', () => {
            panelState.aiSolver = !panelState.aiSolver;
            aiSolver.classList.toggle('active', panelState.aiSolver);
            saveState();
        });

        // Generate & Fill button
        const btnGenerateFill = panel.querySelector('#btn-generate-fill');
        btnGenerateFill?.addEventListener('click', () => {
            generateAndFill();
        });

        // Export button
        const btnExport = panel.querySelector('#btn-export');
        btnExport?.addEventListener('click', () => {
            exportCards();
        });

        // Sync button
        const btnSync = panel.querySelector('#btn-sync');
        btnSync?.addEventListener('click', () => {
            loadState();
            alert('Settings synced!');
        });

        // Clear button
        const btnClear = panel.querySelector('#btn-clear');
        btnClear?.addEventListener('click', () => {
            clearFields();
        });

        // Keyboard shortcut
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'F') {
                e.preventDefault();
                generateAndFill();
            }
        });
    }

    // Generate card from BIN
    function generateCard() {
        const bin = panelState.customBin || getBinForProtocol(panelState.cardProtocol);
        const cardNumber = generateCardNumber(bin);
        const expiry = generateExpiry();
        const cvv = generateCVV();

        panelState.customBin = cardNumber;
        panelState.expiry = expiry;
        panelState.cvv = cvv;
        panelState.history++;

        updatePanelUI();
        saveState();

        return { cardNumber, expiry, cvv };
    }

    // Get BIN for card protocol
    function getBinForProtocol(protocol) {
        const bins = {
            mastercard: ['51', '52', '53', '54', '55'],
            visa: ['4'],
            amex: ['34', '37'],
            discover: ['6011', '65']
        };
        const protocolBins = bins[protocol] || bins.mastercard;
        return protocolBins[Math.floor(Math.random() * protocolBins.length)];
    }

    // Generate card number with Luhn check
    function generateCardNumber(bin) {
        let number = bin;
        const length = bin.startsWith('34') || bin.startsWith('37') ? 15 : 16;

        while (number.length < length - 1) {
            number += Math.floor(Math.random() * 10);
        }

        // Luhn check digit
        number += luhnCheckDigit(number);
        return number;
    }

    // Calculate Luhn check digit
    function luhnCheckDigit(number) {
        let sum = 0;
        for (let i = 0; i < number.length; i++) {
            let digit = parseInt(number[number.length - 1 - i]);
            if (i % 2 === 0) {
                digit *= 2;
                if (digit > 9) digit -= 9;
            }
            sum += digit;
        }
        return (10 - (sum % 10)) % 10;
    }

    // Generate expiry date
    function generateExpiry() {
        const month = String(Math.floor(Math.random() * 12) + 1).padStart(2, '0');
        const year = String(new Date().getFullYear() + Math.floor(Math.random() * 5) + 1).slice(-2);
        return `${month}/${year}`;
    }

    // Generate CVV
    function generateCVV() {
        const length = panelState.cardProtocol === 'amex' ? 4 : 3;
        let cvv = '';
        for (let i = 0; i < length; i++) {
            cvv += Math.floor(Math.random() * 10);
        }
        return cvv;
    }

    // Generate and fill form
    function generateAndFill() {
        const card = generateCard();

        // Try to fill Stripe form
        fillStripeForm(card);

        // Notify success
        showNotification('Card generated and filled!');
    }

    // Fill Stripe form
    function fillStripeForm(card) {
        // Card number
        const cardInputs = document.querySelectorAll([
            'input[name="cardnumber"]',
            'input[name="cardNumber"]',
            'input[autocomplete="cc-number"]',
            'input[data-elements-stable-field-name="cardNumber"]',
            '[name*="card"][name*="number"]'
        ].join(','));

        cardInputs.forEach(input => setInputValue(input, card.cardNumber));

        // Expiry
        const expiryInputs = document.querySelectorAll([
            'input[name="exp-date"]',
            'input[name="cardExpiry"]',
            'input[autocomplete="cc-exp"]',
            'input[data-elements-stable-field-name="cardExpiry"]',
            '[name*="expir"]'
        ].join(','));

        expiryInputs.forEach(input => setInputValue(input, card.expiry));

        // CVV
        const cvvInputs = document.querySelectorAll([
            'input[name="cvc"]',
            'input[name="cardCvc"]',
            'input[autocomplete="cc-csc"]',
            'input[data-elements-stable-field-name="cardCvc"]',
            '[name*="cvc"]', '[name*="cvv"]'
        ].join(','));

        cvvInputs.forEach(input => setInputValue(input, card.cvv));

        // Send message to content script for iframe filling
        window.postMessage({
            type: 'PROPAGANDA_FILL_CARD',
            card: card
        }, '*');
    }

    // Set input value with events
    function setInputValue(input, value) {
        if (!input) return;

        input.focus();
        input.value = value;

        // Trigger events
        ['input', 'change', 'blur'].forEach(eventType => {
            input.dispatchEvent(new Event(eventType, { bubbles: true }));
        });
    }

    // Export cards
    function exportCards() {
        const data = `${panelState.customBin}|${panelState.expiry}|${panelState.cvv}`;
        navigator.clipboard.writeText(data).then(() => {
            showNotification('Card copied to clipboard!');
        });
    }

    // Clear fields
    function clearFields() {
        panelState.customBin = '';
        panelState.expiry = '';
        panelState.cvv = '';
        updatePanelUI();
        saveState();
        showNotification('Fields cleared!');
    }

    // Show notification
    function showNotification(message) {
        const existing = document.querySelector('.propaganda-notification');
        if (existing) existing.remove();

        const notification = document.createElement('div');
        notification.className = 'propaganda-notification';
        notification.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: linear-gradient(135deg, #00ffff, #00cc99);
      color: #000;
      padding: 12px 20px;
      border-radius: 8px;
      font-family: 'Segoe UI', sans-serif;
      font-size: 13px;
      font-weight: 600;
      z-index: 2147483647;
      box-shadow: 0 4px 20px rgba(0, 255, 255, 0.4);
      animation: slideIn 0.3s ease;
    `;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => notification.remove(), 2000);
    }

    // Inject CSS
    function injectStyles() {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = chrome.runtime.getURL('assets/styles/panel-styles.css');
        document.head.appendChild(link);

        // Add notification animation
        const style = document.createElement('style');
        style.textContent = `
      @keyframes slideIn {
        from { transform: translateX(100px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
    `;
        document.head.appendChild(style);
    }

    // Check if Stripe checkout page
    function isStripeCheckout() {
        const url = window.location.href;
        return url.includes('stripe.com') ||
            url.includes('checkout') ||
            url.includes('cs_live_') ||
            url.includes('pay.') ||
            document.querySelector('[data-stripe]') ||
            document.querySelector('form[action*="stripe"]');
    }

    // Initialize
    function init() {
        if (!isStripeCheckout()) {
            // Check again after page loads
            setTimeout(() => {
                if (isStripeCheckout()) initPanel();
            }, 2000);
            return;
        }

        initPanel();
    }

    function initPanel() {
        // Prevent duplicate panels
        if (document.getElementById('propaganda-panel')) return;

        injectStyles();

        const panel = createPanel();
        document.body.appendChild(panel);

        makeDraggable(panel);
        bindEvents(panel);
        loadState();

        console.log('Propaganda Panel: Initialized');
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Also listen for SPA navigation
    let lastUrl = location.href;
    new MutationObserver(() => {
        if (location.href !== lastUrl) {
            lastUrl = location.href;
            setTimeout(init, 1000);
        }
    }).observe(document, { subtree: true, childList: true });

})();
