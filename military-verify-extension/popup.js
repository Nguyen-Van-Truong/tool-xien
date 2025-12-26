// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
  });
});

// ==================== TEXT FORMAT PARSING ====================
// Format: FirstName|LastName|Branch|BirthMonth|BirthDay|BirthYear|DeathMonth|DeathDay|DeathYear|Email

const EMAIL_DOMAINS = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com', 'icloud.com', 'mail.com'];

function generateRandomEmail(firstName, lastName) {
  const domain = EMAIL_DOMAINS[Math.floor(Math.random() * EMAIL_DOMAINS.length)];
  const rand = Math.floor(Math.random() * 999);
  return `${firstName.toLowerCase()}${lastName.toLowerCase()}${rand}@${domain}`;
}

function parseVeteranLine(line) {
  const parts = line.split('|').map(p => p.trim());
  if (parts.length < 6) return null;

  const firstName = parts[0] || '';
  const lastName = parts[1] || '';

  // Map branch names
  let branch = parts[2] || 'Navy';
  if (branch.toUpperCase().includes('NAVY')) branch = 'Navy';
  else if (branch.toUpperCase().includes('ARMY')) branch = 'Army';
  else if (branch.toUpperCase().includes('AIR')) branch = 'Air Force';
  else if (branch.toUpperCase().includes('MARINE')) branch = 'Marine Corps';
  else if (branch.toUpperCase().includes('COAST')) branch = 'Coast Guard';

  return {
    status: 'MILITARY_VETERAN',
    branch: branch,
    firstName: firstName,
    lastName: lastName,
    birthMonth: parts[3] || 'January',
    birthDay: parts[4] || '1',
    birthYear: parts[5] || '1950',
    dischargeMonth: parts[6] || 'January',
    dischargeDay: parts[7] || '1',
    dischargeYear: parts[8] || '2025',
    email: parts[9] || generateRandomEmail(firstName, lastName)
  };
}

function formatVeteranToText(vet) {
  return `${vet.firstName}|${vet.lastName}|${vet.branch}|${vet.birthMonth}|${vet.birthDay}|${vet.birthYear}|${vet.dischargeMonth}|${vet.dischargeDay}|${vet.dischargeYear}|${vet.email}`;
}

// ==================== QUICK FILL TAB ====================
let currentLines = [];
let currentLineIndex = 0;

function updateQuickStatus() {
  document.getElementById('currentLineNum').textContent = currentLineIndex + 1;
  document.getElementById('totalLines').textContent = currentLines.length;

  const currentEl = document.getElementById('currentVeteran');
  if (currentLines.length > 0 && currentLineIndex < currentLines.length) {
    const vet = parseVeteranLine(currentLines[currentLineIndex]);
    if (vet) {
      currentEl.innerHTML = `<strong>${vet.firstName} ${vet.lastName}</strong><br>${vet.branch} | DOB: ${vet.birthMonth} ${vet.birthDay}, ${vet.birthYear}`;
    }
  } else {
    currentEl.innerHTML = '<em>No data</em>';
  }
}

function showQuickStatus(message, isError = false) {
  const statusEl = document.getElementById('quickStatus');
  statusEl.textContent = message;
  statusEl.className = 'status ' + (isError ? 'error' : 'success');
  setTimeout(() => statusEl.className = 'status', 3000);
}

document.getElementById('quickText').addEventListener('input', () => {
  const text = document.getElementById('quickText').value.trim();
  currentLines = text.split('\n').filter(line => line.trim().length > 0);
  currentLineIndex = 0;
  updateQuickStatus();
});

document.getElementById('parseAndFillBtn').addEventListener('click', async () => {
  if (currentLines.length === 0) {
    showQuickStatus('Paste veteran data first!', true);
    return;
  }

  const line = currentLines[currentLineIndex];
  const vet = parseVeteranLine(line);

  if (!vet) {
    showQuickStatus('Invalid format! Use: FirstName|LastName|Branch|...', true);
    return;
  }

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab.url.includes('sheerid.com')) {
      showQuickStatus('Open SheerID page first!', true);
      return;
    }

    await chrome.tabs.sendMessage(tab.id, { action: 'fillForm', data: vet });
    showQuickStatus(`✅ Filled: ${vet.firstName} ${vet.lastName}`);
  } catch (error) {
    console.error(error);
    showQuickStatus('Error! Refresh page and try again.', true);
  }
});

document.getElementById('nextLineBtn').addEventListener('click', async () => {
  if (currentLines.length === 0) return;

  currentLineIndex = (currentLineIndex + 1) % currentLines.length;
  updateQuickStatus();

  // Auto fill next
  const line = currentLines[currentLineIndex];
  const vet = parseVeteranLine(line);

  if (vet) {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab.url.includes('sheerid.com')) {
        await chrome.tabs.sendMessage(tab.id, { action: 'fillForm', data: vet });
        showQuickStatus(`✅ Next: ${vet.firstName} ${vet.lastName}`);
      }
    } catch (e) { }
  }
});

// ==================== VLM TAB ====================
function showVlmStatus(message, isError = false) {
  const statusEl = document.getElementById('vlmStatus');
  statusEl.textContent = message;
  statusEl.className = 'status ' + (isError ? 'error' : 'success');
  setTimeout(() => statusEl.className = 'status', 3000);
}

document.getElementById('scrapeVlmBtn').addEventListener('click', async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab.url.includes('vlm.cem.va.gov')) {
      showVlmStatus('Open VLM page first!', true);
      return;
    }

    const response = await chrome.tabs.sendMessage(tab.id, { action: 'scrapeVeterans' });

    if (response && response.data) {
      const textArea = document.getElementById('vlmData');
      const lines = response.data.map(v =>
        `${v.firstName}|${v.lastName}|${v.branch}|${v.birthMonth}|${v.birthDay}|${v.birthYear}|${v.deathMonth}|${v.deathDay}|${v.deathYear}`
      );
      textArea.value = lines.join('\n');
      showVlmStatus(`✅ Scraped ${response.data.length} veterans!`);
    }
  } catch (error) {
    console.error(error);
    showVlmStatus('Error! Make sure you are on VLM page.', true);
  }
});

document.getElementById('copyVlmBtn').addEventListener('click', () => {
  const textArea = document.getElementById('vlmData');
  navigator.clipboard.writeText(textArea.value);
  showVlmStatus('📋 Copied to clipboard!');
});

document.getElementById('openVlmSearchBtn').addEventListener('click', () => {
  const lastName = document.getElementById('vlmLastName').value.trim() || 'b';
  const branch = document.getElementById('vlmBranch').value;
  const deathYear = document.getElementById('vlmDeathYear').value || '2025';

  let url = `https://www.vlm.cem.va.gov/?lastName=${encodeURIComponent(lastName)}`;
  if (branch) url += `&branch=${encodeURIComponent(branch)}`;
  if (deathYear) url += `&yearOfDeath=${deathYear}`;

  chrome.tabs.create({ url });
});

document.getElementById('clearVlmBtn').addEventListener('click', () => {
  document.getElementById('vlmData').value = '';
});

// ==================== MANUAL FILL TAB ====================
function getFormData() {
  return {
    status: document.getElementById('status').value,
    branch: document.getElementById('branch').value,
    firstName: document.getElementById('firstName').value.trim(),
    lastName: document.getElementById('lastName').value.trim(),
    birthMonth: document.getElementById('birthMonth').value,
    birthDay: document.getElementById('birthDay').value,
    birthYear: document.getElementById('birthYear').value,
    dischargeMonth: document.getElementById('dischargeMonth').value,
    dischargeDay: document.getElementById('dischargeDay').value,
    dischargeYear: document.getElementById('dischargeYear').value,
    email: document.getElementById('email').value.trim()
  };
}

function setFormData(data) {
  if (data.status) document.getElementById('status').value = data.status;
  if (data.branch) document.getElementById('branch').value = data.branch;
  if (data.firstName) document.getElementById('firstName').value = data.firstName;
  if (data.lastName) document.getElementById('lastName').value = data.lastName;
  if (data.birthMonth) document.getElementById('birthMonth').value = data.birthMonth;
  if (data.birthDay) document.getElementById('birthDay').value = data.birthDay;
  if (data.birthYear) document.getElementById('birthYear').value = data.birthYear;
  if (data.dischargeMonth) document.getElementById('dischargeMonth').value = data.dischargeMonth;
  if (data.dischargeDay) document.getElementById('dischargeDay').value = data.dischargeDay;
  if (data.dischargeYear) document.getElementById('dischargeYear').value = data.dischargeYear;
  if (data.email) document.getElementById('email').value = data.email;
}

function showFillStatus(message, isError = false) {
  const statusEl = document.getElementById('fillStatus');
  statusEl.textContent = message;
  statusEl.className = 'status ' + (isError ? 'error' : 'success');
  setTimeout(() => statusEl.className = 'status', 3000);
}

document.getElementById('fillBtn').addEventListener('click', async () => {
  const data = getFormData();

  if (!data.firstName || !data.lastName) {
    showFillStatus('Enter first and last name!', true);
    return;
  }

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab.url.includes('sheerid.com')) {
      showFillStatus('Open SheerID page first!', true);
      return;
    }

    await chrome.tabs.sendMessage(tab.id, { action: 'fillForm', data });
    showFillStatus('✅ Form filled!');
  } catch (error) {
    console.error(error);
    showFillStatus('Error! Refresh page.', true);
  }
});

document.getElementById('saveBtn').addEventListener('click', async () => {
  const data = getFormData();

  if (!data.firstName || !data.lastName) {
    showFillStatus('Enter first and last name!', true);
    return;
  }

  const result = await chrome.storage.local.get(['veterans']);
  const veterans = result.veterans || [];

  data.id = Date.now();
  data.savedAt = new Date().toISOString();
  veterans.push(data);

  await chrome.storage.local.set({ veterans });
  showFillStatus('✅ Saved!');
  loadVeteranList();
});

// ==================== SAVED DATA TAB ====================
async function loadVeteranList() {
  const result = await chrome.storage.local.get(['veterans']);
  const veterans = result.veterans || [];

  document.getElementById('veteranCount').textContent = veterans.length;

  const listEl = document.getElementById('veteranList');
  listEl.innerHTML = '';

  veterans.slice(-20).reverse().forEach((vet, index) => {
    const realIndex = veterans.length - 1 - index;
    const item = document.createElement('div');
    item.className = 'veteran-item';
    item.innerHTML = `
      <div class="veteran-name">${vet.firstName} ${vet.lastName}</div>
      <div class="veteran-info">${vet.branch} | ${vet.birthYear}</div>
      <div class="veteran-actions">
        <button class="btn secondary use-btn" data-index="${realIndex}">Use</button>
        <button class="btn danger delete-btn" data-index="${realIndex}">×</button>
      </div>
    `;
    listEl.appendChild(item);
  });

  document.querySelectorAll('.use-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const index = parseInt(btn.dataset.index);
      const result = await chrome.storage.local.get(['veterans']);
      const vet = result.veterans[index];
      setFormData(vet);
      document.querySelector('[data-tab="fill"]').click();
    });
  });

  document.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const index = parseInt(btn.dataset.index);
      const result = await chrome.storage.local.get(['veterans']);
      const veterans = result.veterans || [];
      veterans.splice(index, 1);
      await chrome.storage.local.set({ veterans });
      loadVeteranList();
    });
  });
}

document.getElementById('importBtn').addEventListener('click', () => {
  document.getElementById('importFile').click();
});

document.getElementById('importFile').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  try {
    const text = await file.text();

    // Check if JSON or text format
    if (file.name.endsWith('.json')) {
      const data = JSON.parse(text);
      if (Array.isArray(data)) {
        const result = await chrome.storage.local.get(['veterans']);
        const veterans = result.veterans || [];
        data.forEach(vet => {
          vet.id = Date.now() + Math.random();
          vet.savedAt = new Date().toISOString();
          veterans.push(vet);
        });
        await chrome.storage.local.set({ veterans });
        loadVeteranList();
        alert(`Imported ${data.length} veterans!`);
      }
    } else {
      // Text format - each line is a veteran
      const lines = text.split('\n').filter(l => l.trim());
      const result = await chrome.storage.local.get(['veterans']);
      const veterans = result.veterans || [];
      let count = 0;
      lines.forEach(line => {
        const vet = parseVeteranLine(line);
        if (vet) {
          vet.id = Date.now() + Math.random();
          vet.savedAt = new Date().toISOString();
          veterans.push(vet);
          count++;
        }
      });
      await chrome.storage.local.set({ veterans });
      loadVeteranList();
      alert(`Imported ${count} veterans!`);
    }
  } catch (error) {
    alert('Error importing: ' + error.message);
  }

  e.target.value = '';
});

document.getElementById('exportBtn').addEventListener('click', async () => {
  const result = await chrome.storage.local.get(['veterans']);
  const veterans = result.veterans || [];

  const blob = new Blob([JSON.stringify(veterans, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = `veterans_${new Date().toISOString().split('T')[0]}.json`;
  a.click();

  URL.revokeObjectURL(url);
});

document.getElementById('exportTextBtn').addEventListener('click', async () => {
  const result = await chrome.storage.local.get(['veterans']);
  const veterans = result.veterans || [];

  const text = veterans.map(formatVeteranToText).join('\n');

  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = `veterans_${new Date().toISOString().split('T')[0]}.txt`;
  a.click();

  URL.revokeObjectURL(url);
});

document.getElementById('clearBtn').addEventListener('click', async () => {
  if (confirm('Delete all saved veterans?')) {
    await chrome.storage.local.set({ veterans: [] });
    loadVeteranList();
  }
});

// Initialize
loadVeteranList();
updateQuickStatus();
