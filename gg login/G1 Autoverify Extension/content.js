// Helper: Delay
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

// Định nghĩa trường mục tiêu cần chọn chính xác trong dropdown School
const TARGET_SCHOOL = {
  name: "Professional Beauty School",
  city: "Yakima",
  state: "WA",
  country: "US",
  type: "POST_SECONDARY"
};

// SheerID "organization" object - giống main.py (gửi thẳng ID để chọn đúng)
const TARGET_ORGANIZATION = {
  id: 4078280,
  idExtended: "4078280",
  name: "Professional Beauty School"
};

// BẬT chế độ "giống main.py": chỉ dùng API, không fallback dropdown
const USE_API_ORG_SELECTION_ONLY = true;

function getVerificationIdFromUrl() {
  try {
    const url = new URL(window.location.href);
    return url.searchParams.get("verificationId");
  } catch {
    return null;
  }
}

async function sha256Hex(input) {
  const enc = new TextEncoder().encode(input);
  const buf = await crypto.subtle.digest("SHA-256", enc);
  return Array.from(new Uint8Array(buf))
    .map(b => b.toString(16).padStart(2, "0"))
    .join("");
}

async function generateDeviceFingerprintHash() {
  // Không cần giống hệt main.py (MD5), chỉ cần chuỗi hash ổn định/realistic
  const parts = [
    String(Date.now()),
    navigator.userAgent || "",
    navigator.language || "",
    String(screen?.width || ""),
    String(screen?.height || ""),
    String(Math.random())
  ].join("|");
  return sha256Hex(parts);
}

async function sheeridRequest(method, endpoint, body) {
  const url = `https://services.sheerid.com/rest/v2${endpoint}`;
  const resp = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: body ? JSON.stringify(body) : undefined
  });
  let data = null;
  try {
    data = await resp.json();
  } catch {
    data = { _text: await resp.text().catch(() => "") };
  }
  return { status: resp.status, data };
}

function pad2(n) {
  return String(n).padStart(2, "0");
}

function toIsoBirthDate(profile) {
  // main.py dùng yyyy-mm-dd, SheerID API thường expect format này
  if (profile?.birthYear && profile?.birthMonth && profile?.birthDay) {
    return `${profile.birthYear}-${pad2(profile.birthMonth)}-${pad2(profile.birthDay)}`;
  }
  // fallback parse mm/dd/yyyy
  const s = String(profile?.birthDate || "").trim();
  const m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (m) {
    const mm = pad2(m[1]);
    const dd = pad2(m[2]);
    const yyyy = m[3];
    return `${yyyy}-${mm}-${dd}`;
  }
  return s; // cuối cùng: giữ nguyên nếu không parse được
}

async function submitStudentInfoViaApi(profile) {
  const vid = getVerificationIdFromUrl();
  if (!vid) return { ok: false, error: "Không tìm thấy verificationId trên URL" };

  // 1) Check current step
  const check = await sheeridRequest("GET", `/verification/${vid}`);
  if (check.status !== 200) {
    return { ok: false, error: `GET verification failed: HTTP ${check.status}`, payload: check.data };
  }

  const currentStep = check.data?.currentStep || "";
  if (currentStep && currentStep !== "collectStudentPersonalInfo") {
    // Nếu đã qua bước này (docUpload / sso / ...) thì ok luôn
    return { ok: true, currentStep, payload: check.data };
  }

  // 2) Submit collectStudentPersonalInfo giống main.py (ép organization theo ID)
  const fingerprintHash = await generateDeviceFingerprintHash();
  const body = {
    firstName: profile.firstName,
    lastName: profile.lastName,
    birthDate: toIsoBirthDate(profile),
    email: profile.email,
    phoneNumber: "",
    organization: { ...TARGET_ORGANIZATION },
    deviceFingerprintHash: fingerprintHash,
    locale: "en-US",
    metadata: {
      verificationId: vid
    }
  };

  const submit = await sheeridRequest("POST", `/verification/${vid}/step/collectStudentPersonalInfo`, body);
  if (submit.status !== 200) {
    return { ok: false, error: `Submit failed: HTTP ${submit.status}`, payload: submit.data };
  }

  return { ok: true, currentStep: submit.data?.currentStep || "", payload: submit.data };
}

// Helper: Simulate typing (clear trước rồi gõ lại toàn bộ text)
async function simulateTyping(element, text) {
  element.focus();
  element.value = "";
  const eventInput = new Event('input', { bubbles: true });
  element.dispatchEvent(eventInput);

  for (let i = 0; i < text.length; i++) {
    element.value += text[i];
    element.dispatchEvent(new Event('input', { bubbles: true }));
    // await delay(10); // Typing speed
  }

  element.dispatchEvent(new Event('change', { bubbles: true }));
  element.blur();
}

// Helper: Simulate typing but CHỈ gõ tiếp (không xóa giá trị hiện tại)
async function simulateTypingAppend(element, text) {
  element.focus();
  for (let i = 0; i < text.length; i++) {
    element.value += text[i];
    element.dispatchEvent(new Event('input', { bubbles: true }));
    // await delay(10); // Typing speed
  }
  element.dispatchEvent(new Event('change', { bubbles: true }));
  element.blur();
}

// Helper: Select from custom dropdown (for Country and College)
async function selectCustomDropdown(inputSelector, value) {
  const input = document.querySelector(inputSelector);
  if (!input) {
    console.error(`Element not found: ${inputSelector}`);
    return;
  }

  // Bước 1: Bấm chữ cái đầu tiên vào ô input -> một modal mới hiện ra
  input.click();
  input.focus();
  await delay(300);
  
  // Gõ ký tự đầu tiên để mở modal
  const firstChar = value.charAt(0);
  await simulateTyping(input, firstChar);
  await delay(1500); // Chờ modal xuất hiện (tăng delay để modal có thời gian hiện ra)

  // Bước 2: Tìm ô search trong modal vừa hiện ra
  // Tìm các input có thể là ô search trong modal (thường có placeholder chứa "search" hoặc "tìm")
  let searchInput = null;
  
  // Thử các selector phổ biến cho ô search trong modal
  const searchSelectors = [
    'input[type="text"][placeholder*="search" i]',
    'input[type="text"][placeholder*="tìm" i]',
    'input[type="search"]',
    '.modal input[type="text"]',
    '[role="dialog"] input[type="text"]',
    '.dropdown-menu input',
    'input[aria-label*="search" i]',
    'input[aria-label*="tìm" i]'
  ];

  for (const selector of searchSelectors) {
    const found = document.querySelector(selector);
    if (found && found !== input && found.offsetParent !== null) {
      searchInput = found;
      console.log(`Found search input: ${selector}`);
      break;
    }
  }

  // Nếu không tìm thấy bằng selector, tìm input text đầu tiên trong modal/dialog
  if (!searchInput) {
    const modal = document.querySelector('.modal, [role="dialog"], .dropdown-menu, .popover');
    if (modal) {
      const inputs = modal.querySelectorAll('input[type="text"], input[type="search"]');
      for (const inp of inputs) {
        if (inp !== input && inp.offsetParent !== null) {
          searchInput = inp;
          console.log('Found search input in modal');
          break;
        }
      }
    }
  }

  // Bước 3: Nhập tên trường vào ô search trong modal
  if (searchInput) {
    searchInput.focus();
    await delay(300); // Delay trước khi nhập
    // Ví dụ: value = "Professional Beauty School"
    // Bước 1 đã gõ chữ đầu tiên "P" để mở modal.
    // Ở đây ta CHỈ gõ tiếp các ký tự sau "P" (\"rofessional Beauty School\")
    let textToType = value;
    const currentVal = searchInput.value || "";
    if (currentVal.length === 1 && currentVal[0].toLowerCase() === firstChar.toLowerCase()) {
      textToType = value.slice(1); // chỉ gõ phần còn lại sau chữ đầu tiên
    }
    await simulateTypingAppend(searchInput, textToType);
    await delay(1500); // Chờ dữ liệu load đầy đủ (tăng delay để danh sách kết quả load xong)
  } else {
    console.warn('Search input in modal not found, falling back to original input');
    // Fallback: nếu không tìm thấy ô search trong modal, thử nhập vào input gốc
    await simulateTyping(input, value);
    await delay(1500); // Tăng delay cho fallback cũng
  }

  // Bước 4: Chọn đúng trường trong danh sách vừa tìm kiếm
  // Tìm menu/dropdown list chứa các option
  const menuId = input.getAttribute('aria-controls');
  let firstOption = null;

  if (menuId) {
    const optionSelector = `#${menuId} [role="option"]:not([aria-disabled="true"])`;
    const options = Array.from(document.querySelectorAll(optionSelector));

    if (options.length > 0) {
      // Nếu là dropdown School (#sid-college-name) thì cố gắng ép chọn đúng trường TARGET_SCHOOL
      if (inputSelector === "#sid-college-name") {
        const targetName = (TARGET_SCHOOL.name || value || "").toLowerCase();
        const targetCity = (TARGET_SCHOOL.city || "").toLowerCase();
        const targetState = (TARGET_SCHOOL.state || "").toLowerCase();

        let exactMatch = null;
        let nameMatch = null;

        for (const opt of options) {
          const txt = (opt.innerText || opt.textContent || "").toLowerCase();

          // Ưu tiên: khớp cả name + city + state
          if (txt.includes(targetName) && txt.includes(targetCity) && txt.includes(targetState)) {
            exactMatch = opt;
            break;
          }

          // Thứ hai: khớp name + state
          if (!exactMatch && txt.includes(targetName) && txt.includes(targetState)) {
            exactMatch = opt;
          }

          // Thứ ba: khớp name
          if (!nameMatch && txt.includes(targetName)) {
            nameMatch = opt;
          }
        }

        firstOption = exactMatch || nameMatch || options[0];
      } else {
        // Các dropdown khác (ví dụ tháng sinh) vẫn chọn option đầu tiên như cũ
        firstOption = options[0];
      }
    }
  }

  // Nếu không tìm thấy bằng menuId, tìm trong modal
  if (!firstOption) {
    const modal = document.querySelector('.modal, [role="dialog"], .dropdown-menu, .popover');
    if (modal) {
      firstOption = modal.querySelector('[role="option"]:not([aria-disabled="true"]), .option:first-child, li:first-child');
    }
  }

  // Fallback: tìm bất kỳ option nào trong document
  if (!firstOption) {
    firstOption = document.querySelector('[role="option"]:not([aria-disabled="true"])');
  }

  if (firstOption) {
    console.log('Clicking option:', firstOption.textContent);
    await delay(300); // Delay trước khi click để đảm bảo option đã sẵn sàng
    firstOption.click();
  } else {
    console.warn('No option found, trying Enter key');
    // Fallback: simulate Enter key
    await delay(300);
    const targetInput = searchInput || input;
    targetInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
  }

  await delay(500); // Delay sau khi chọn để form xử lý
}

// ===== LANGUAGE DETECTION =====
function detectLanguage() {
  const bodyText = document.body.innerText;

  // Check for specific Vietnamese text
  if (bodyText.includes("Xác minh tư cách sinh viên của bạn")) {
    return false; // isEnglish = false -> Vietnamese
  }

  // Check for specific English text
  if (bodyText.includes("Verify your student status")) {
    return true; // isEnglish = true -> English
  }

  // Fallback: Check HTML lang attribute
  const lang = document.documentElement.lang || "";
  if (lang.toLowerCase().startsWith("vi")) return false;

  // Default to English if no strong signal for Vietnamese
  return true;
}

async function fillSheerIDForm(profile) {
  console.log("Starting to fill form...");
  const isEnglish = detectLanguage();
  console.log("Detected Language: " + (isEnglish ? "English" : "Vietnamese"));

  // ƯU TIÊN: dùng API giống main.py để ép chọn đúng organization theo ID
  // Nếu API fail thì fallback về cách điền UI
  try {
    const apiRes = await submitStudentInfoViaApi(profile);
    if (apiRes.ok) {
      console.log("Submitted student info via API. Current step:", apiRes.currentStep);
      // API OK => luôn reload để UI đồng bộ sang bước tiếp theo (docUpload / sso / ...)
      await delay(1500);
      window.location.reload();
      return;
    } else {
      console.warn("API submit failed:", apiRes.error, apiRes.payload);
      // Báo lỗi + thả nút, KHÔNG fallback dropdown (giống main.py)
      if (USE_API_ORG_SELECTION_ONLY) {
        chrome.storage.local.set({
          verificationStatus: "error",
          lastApiError: { error: apiRes.error, payload: apiRes.payload }
        });
        // thả nút về trạng thái mặc định sau vài giây (nếu muốn)
        setTimeout(() => chrome.storage.local.remove("verificationStatus"), 4000);
        return;
      }
    }
  } catch (e) {
    console.warn("API submit exception:", e);
    if (USE_API_ORG_SELECTION_ONLY) {
      chrome.storage.local.set({
        verificationStatus: "error",
        lastApiError: { error: String(e) }
      });
      setTimeout(() => chrome.storage.local.remove("verificationStatus"), 4000);
      return;
    }
  }

  // Country: mặc định US trên SheerID, không cần chọn.

  // 1. Đại học/Cao đẳng
  // Tên trường thường không đổi, nhưng nếu có mapping tên tiếng Anh thì cần xử lý.
  // Hiện tại giữ nguyên tên tiếng Việt vì trường ở VN.
  await selectCustomDropdown("#sid-college-name", profile.collegeName);
  console.log("Filled College");

  // 2. Tên (First Name)
  const firstNameInput = document.querySelector("#sid-first-name");
  if (firstNameInput) await simulateTyping(firstNameInput, profile.firstName);

  // 3. Họ (Last Name)
  const lastNameInput = document.querySelector("#sid-last-name");
  if (lastNameInput) await simulateTyping(lastNameInput, profile.lastName);

  // 4. Ngày sinh
  // Ngày
  const dayInput = document.querySelector("#sid-birthdate-day");
  if (dayInput) await simulateTyping(dayInput, profile.birthDay);

  // Tháng sinh — luôn tiếng Anh (US): January, February, March, ...
  const MONTHS_EN = {
    "01": "January", "02": "February", "03": "March",
    "04": "April", "05": "May", "06": "June",
    "07": "July", "08": "August", "09": "September",
    "10": "October", "11": "November", "12": "December"
  };
  const monthStr = MONTHS_EN[profile.birthMonth] || profile.birthMonth;
  await selectCustomDropdown("#sid-birthdate__month", monthStr);

  // Năm
  const yearInput = document.querySelector("#sid-birthdate-year");
  if (yearInput) await simulateTyping(yearInput, profile.birthYear);

  // 5. Email
  const emailInput = document.querySelector("#sid-email");
  if (emailInput) await simulateTyping(emailInput, profile.email);

  console.log("Form filling completed.");

  // 6. Auto Submit
  await delay(800); // Chờ một chút để validation chạy xong
  const submitBtn = document.querySelector("#sid-submit-wrapper__collect-info");
  if (submitBtn) {
    console.log("Clicking submit button...");
    // Đánh dấu thời điểm submit
    submitTime = Date.now();
    submitBtn.click();
    // Logic kiểm tra sau submit được xử lý trong monitorPageChanges()
  } else {
    console.warn("Submit button not found!");
    // Nếu không tìm thấy nút submit, reset luôn
    chrome.storage.local.remove("verificationStatus");
  }
}

// Lắng nghe message từ popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "FILL_SHEERID_AND_SUBMIT") {
    const profile = message.profile;

    // Thực thi async function
    fillSheerIDForm(profile).then(() => {
      sendResponse({ status: "done" });
    }).catch(err => {
      console.error("Error filling form:", err);
      sendResponse({ status: "error" });
    });

    return true; // Keep channel open for async response
  }
});

// ===== AUTO UPLOAD & STATUS MONITOR LOGIC =====
// Chuyển Base64 thành File object
function dataURLtoFile(dataurl, filename) {
  var arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
    bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new File([u8arr], filename, { type: mime });
}

function checkPageStatus() {
  const bodyText = document.body.innerText;

  // 1. Check Success
  if (bodyText.includes("Bạn đã được xác minh") || bodyText.includes("Success") || bodyText.includes("verified")) {
    chrome.storage.local.set({ verificationStatus: "success" });
    return;
  }

  // 2. Check Reviewing
  if (bodyText.includes("Đang kiểm tra") || bodyText.includes("Reviewing")) {
    chrome.storage.local.set({ verificationStatus: "reviewing" });
    return;
  }

  // 3. Check Error - Phát hiện các thông báo lỗi
  const errorMessages = [
    "We are unable to verify you at this time",
    "unable to verify",
    "Error",
    "error occurred",
    "verification failed",
    "Không thể xác minh",
    "Lỗi xác minh"
  ];
  
  const hasError = errorMessages.some(msg => bodyText.toLowerCase().includes(msg.toLowerCase()));
  if (hasError) {
    console.log("Error detected on page, resetting button");
    chrome.storage.local.set({ verificationStatus: "error" });
    // Reset nút về trạng thái ban đầu sau một chút
    setTimeout(() => {
      chrome.storage.local.remove("verificationStatus");
    }, 2000);
    return;
  }

  // 4. Check Upload Step - Nếu có file input thì đang ở bước upload (tiếp tục flow)
  const fileInput = document.querySelector('input[type="file"]');
  if (fileInput) {
    // Đang ở bước upload, không reset nút
    return;
  }

  // 5. Check Initial Form (Reset) - Nếu vẫn ở form ban đầu sau khi submit
  const countryInput = document.querySelector("#sid-country");
  const submitBtn = document.querySelector("#sid-submit-wrapper__collect-info");
  if (countryInput || submitBtn) {
    chrome.storage.local.get("verificationStatus", (data) => {
      // Nếu đang processing và vẫn ở form ban đầu sau một khoảng thời gian
      // => có thể submit thất bại hoặc không chuyển trang
      if (data.verificationStatus === "processing") {
        // Kiểm tra xem có thông báo lỗi validation không
        const hasValidationError = document.querySelector('.error, .alert-danger, [role="alert"]');
        if (hasValidationError) {
          console.log("Validation error detected, resetting button");
          chrome.storage.local.remove("verificationStatus");
        }
      } else if (data.verificationStatus !== "processing") {
        chrome.storage.local.remove("verificationStatus");
      }
    });
  }
}

// Biến global để lưu thời điểm submit
let submitTime = null;

function monitorPageChanges() {
  const runChecks = () => {
    // 1. Auto Upload Check
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
      // Nếu có file input, đã chuyển sang bước upload → tiếp tục flow
      if (submitTime) {
        console.log("Successfully moved to upload step");
        submitTime = null; // Reset timer
      }
      
      chrome.storage.local.get("pendingUploadImage", (data) => {
        if (data.pendingUploadImage) {
          console.log("Found pending image, uploading...");
          try {
            const file = dataURLtoFile(data.pendingUploadImage, "student_card.png");

            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;

            fileInput.dispatchEvent(new Event('change', { bubbles: true }));
            fileInput.dispatchEvent(new Event('input', { bubbles: true }));

            console.log("Auto-upload completed!");
            chrome.storage.local.remove("pendingUploadImage");

            // Tự động bấm nút Gửi
            setTimeout(() => {
              const submitDocBtn = document.querySelector("#sid-submit-doc-upload");
              if (submitDocBtn) submitDocBtn.click();
            }, 1500);
          } catch (e) {
            console.error("Upload failed:", e);
          }
        }
      });
    }

    // 2. Status Check
    checkPageStatus();
    
    // 3. Kiểm tra timeout sau khi submit (nếu đã submit nhưng không chuyển sang upload sau 5 giây)
    if (submitTime) {
      const timeSinceSubmit = Date.now() - submitTime;
      if (timeSinceSubmit > 5000) {
        const fileInputCheck = document.querySelector('input[type="file"]');
        const submitBtnStillExists = document.querySelector("#sid-submit-wrapper__collect-info");
        
        // Nếu vẫn không có file input và vẫn còn nút submit => không chuyển trang
        if (!fileInputCheck && submitBtnStillExists) {
          console.log("Timeout: Submit did not proceed to upload step, resetting button");
          chrome.storage.local.remove("verificationStatus");
          submitTime = null;
        } else if (fileInputCheck) {
          // Đã chuyển sang upload, reset timer
          submitTime = null;
        }
      }
    }
  };

  runChecks();

  const observer = new MutationObserver((mutations) => {
    runChecks();
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
  
  // Lắng nghe khi submit để đánh dấu thời điểm (chỉ thêm một lần)
  if (!window.submitListenerAdded) {
    document.addEventListener('click', (e) => {
      const submitBtn = e.target.closest('#sid-submit-wrapper__collect-info');
      if (submitBtn) {
        submitTime = Date.now();
        console.log("Submit button clicked, starting timeout check");
      }
    }, true);
    window.submitListenerAdded = true;
  }
}

// Chạy monitor
monitorPageChanges();
