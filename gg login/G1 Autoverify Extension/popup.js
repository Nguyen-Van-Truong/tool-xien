// ===== CẤU HÌNH CỐ ĐỊNH =====
const COUNTRY = "United States";
const COLLEGE_NAME = "Professional Beauty School";
const EMAIL_DOMAIN = "@professionalbeautyschool.com";
const PHOI_NAM = "phoinam.png";
const PHOI_NU = "phoinu.png";

// Cấu hình vị trí vẽ text (Copy chính xác từ script.py)
// x_ratio, y_ratio: tỷ lệ so với kích thước ảnh (0–1)
// font_size: kích thước font gốc
// Mặc định vị trí X-Y và font (đã chỉnh cho phôi Professional Beauty School)
const CARD_CONFIG_DEFAULT = {
  ho_ten: {
    x_ratio: 0.54,
    y_ratio: 0.465,
    font_size: 28,
    bold: true,
    color: "#000000"
  },
  ngay_sinh: {
    x_ratio: 0.57,
    y_ratio: 0.533,
    font_size: 28,
    bold: true,
    color: "#000000"
  },
  chuyen_nganh: {
    x_ratio: 0.49,
    y_ratio: 0.599,
    font_size: 28,
    bold: true,
    color: "#000000"
  },
  ma_sinh_vien: {
    x_ratio: 0.5538,
    y_ratio: 0.666,
    font_size: 28,
    bold: true,
    color: "#000000"
  },
  thoi_han_the: {
    x_ratio: 0.5537,
    y_ratio: 0.739,
    font_size: 24,
    bold: true,
    color: "#000000"
  },
  email: {
    x_ratio: 0.23,
    y_ratio: 0.82,
    font_size: 15,
    bold: false,
    color: "#000000"
  }
};

// Cấu hình đang dùng (có thể chỉnh trong chế độ X-Y, lưu vào storage)
let cardConfig = JSON.parse(JSON.stringify(CARD_CONFIG_DEFAULT));

// Trang test: mở bằng chrome-extension://id/index.html → luôn hiển thị giao diện chính
const IS_TEST_PAGE = typeof window !== "undefined" && window.location && window.location.href && window.location.href.indexOf("index.html") > -1;

// ===== HÀM RANDOM DỮ LIỆU (mô phỏng từ code Python) =====
function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomChoice(arr) {
  return arr[randomInt(0, arr.length - 1)];
}

// Dữ liệu mẫu - chuẩn U.S (First Name + Last Name)
const LAST_NAMES_US = [
  "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
  "Rodriguez", "Martinez", "Wilson", "Anderson", "Taylor", "Thomas", "Moore",
  "Jackson", "Martin", "Lee", "Thompson", "White", "Harris", "Clark", "Lewis"
];

const FIRST_NAMES_MALE_US = [
  "James", "Michael", "Robert", "David", "William", "Joseph", "Christopher",
  "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew"
];

const FIRST_NAMES_FEMALE_US = [
  "Mary", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica",
  "Sarah", "Karen", "Lisa", "Nancy", "Betty", "Margaret", "Sandra", "Ashley"
];

const MAJORS_US = [
  "Cosmetology", "Esthetics", "Nail Technology", "Barbering", "Makeup Artistry",
  "Skin Care", "Hair Design", "Massage Therapy", "Salon Management"
];

function randomGender() {
  return Math.random() < 0.5 ? "male" : "female";
}

// US format: First Name (given) + Last Name (family)
function randomName(gender) {
  const lastName = randomChoice(LAST_NAMES_US);
  const firstName = gender === "male"
    ? randomChoice(FIRST_NAMES_MALE_US)
    : randomChoice(FIRST_NAMES_FEMALE_US);
  const fullName = `${firstName} ${lastName}`;
  return {
    fullName,
    lastName,
    firstName
  };
}

function randomBirthDate() {
  const now = new Date();
  const currentYear = now.getFullYear();
  const age = randomInt(18, 25);
  const year = currentYear - age;
  const month = randomInt(1, 12);
  const maxDay = [1, 3, 5, 7, 8, 10, 12].includes(month) ? 31 : (month === 2 ? 28 : 30);
  const day = randomInt(1, maxDay);

  const pad = n => n.toString().padStart(2, "0");

  return {
    day: pad(day),
    month: pad(month),
    year: year.toString(),
    formatted: `${pad(month)}/${pad(day)}/${year}` // US: mm/dd/yyyy
  };
}

function randomStudentId() {
  // Format: YY + 6 số (ví dụ: 24123456)
  const year = randomInt(20, 25);
  const randNum = randomInt(0, 999999).toString().padStart(6, "0");
  return `${year}${randNum}`;
}

function randomCardDuration() {
  const startYear = randomChoice([2024, 2025]);
  const endYear = startYear + 4;
  const startMonth = randomChoice([8, 9, 10]);
  const pad = n => n.toString().padStart(2, "0");
  return `${pad(startMonth)}/${startYear} - ${pad(startMonth)}/${endYear}`;
}

// Tạo profile đầy đủ
function generateRandomProfile() {
  const gender = randomGender();
  const nameData = randomName(gender);
  const dob = randomBirthDate();
  const studentId = randomStudentId();
  const major = randomChoice(MAJORS_US);
  const cardDuration = randomCardDuration();
  const email = studentId + EMAIL_DOMAIN;

  return {
    country: COUNTRY,
    collegeName: COLLEGE_NAME,
    fullName: nameData.fullName,
    lastName: nameData.lastName,
    firstName: nameData.firstName,
    birthDate: dob.formatted,
    birthDay: dob.day,
    birthMonth: dob.month,
    birthYear: dob.year,
    email,
    studentId,
    gender,
    major,
    cardDuration
  };
}

// ===== PRELOAD 2 PHÔI ẢNH =====
const phoiNamImg = new Image();
phoiNamImg.src = chrome.runtime.getURL(PHOI_NAM);

const phoiNuImg = new Image();
phoiNuImg.src = chrome.runtime.getURL(PHOI_NU);

let phoiNamLoaded = false;
let phoiNuLoaded = false;

phoiNamImg.onload = () => { phoiNamLoaded = true; };
phoiNuImg.onload = () => { phoiNuLoaded = true; };

// ===== VẼ THẺ SINH VIÊN LÊN CANVAS =====
function drawCard(profile) {
  const canvas = document.getElementById("cardCanvas");
  const ctx = canvas.getContext("2d");

  // Chọn phôi theo giới tính
  const isMale = profile.gender === "male";
  const img = isMale ? phoiNamImg : phoiNuImg;
  const imgLoaded = isMale ? phoiNamLoaded : phoiNuLoaded;

  // Nếu phôi chưa load xong, chờ một chút
  if (!imgLoaded) {
    // Tạm thời set kích thước nhỏ để hiển thị loading
    canvas.width = 480;
    canvas.height = 270;
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = "#000000";
    ctx.font = "12px Arial";
    ctx.fillText("Đang tải phôi thẻ...", 20, 30);
    setTimeout(() => drawCard(profile), 200);
    return;
  }

  // Set kích thước canvas bằng kích thước thật của ảnh
  canvas.width = img.width;
  canvas.height = img.height;

  const w = canvas.width;
  const h = canvas.height;

  // Vẽ nền (ảnh gốc)
  ctx.clearRect(0, 0, w, h);
  ctx.drawImage(img, 0, 0, w, h);

  // Chuẩn bị dữ liệu để vẽ text (email dùng domain @professionalbeautyschool.com)
  const textData = {
    ho_ten: profile.fullName,
    ngay_sinh: profile.birthDate,
    chuyen_nganh: profile.major,
    ma_sinh_vien: profile.studentId,
    thoi_han_the: profile.cardDuration,
    email: profile.email
  };

  // Hệ số điều chỉnh vị trí Y (đẩy xuống một chút để khớp dòng kẻ)
  const Y_OFFSET_CORRECTION = 0.008;

  // Vẽ từng trường thông tin theo config (dùng cardConfig để hỗ trợ phôi khác)
  Object.keys(cardConfig).forEach(key => {
    const config = cardConfig[key];
    const text = textData[key];

    if (text) {
      // Tính tọa độ trên canvas (giờ là kích thước thật)
      const x = w * config.x_ratio;
      const y = h * (config.y_ratio + Y_OFFSET_CORRECTION);

      // Font size gốc (không cần scale vì đang vẽ trên kích thước gốc)
      const fontSize = config.font_size;

      // Set font style
      const fontWeight = config.bold ? "bold" : "normal";
      ctx.font = `${fontWeight} ${fontSize}px Arial`;
      ctx.fillStyle = config.color;
      ctx.textAlign = "left";
      ctx.textBaseline = "top";

      ctx.fillText(text, x, y);
    }
  });
}

// ===== CẬP NHẬT UI POPUP =====
let currentProfile = null;

function updatePopup(profile) {
  // Cập nhật các trường text trong popup (nếu có element tương ứng)
  const setContent = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };

  setContent("country", profile.country);
  setContent("collegeName", profile.collegeName);
  setContent("lastName", profile.lastName); // Chỉ để hiển thị debug nếu cần
  setContent("firstName", profile.firstName);
  setContent("birthDate", profile.birthDate);
  setContent("email", profile.email);

  // Vẽ lại thẻ
  drawCard(profile);
}

// ===== CHẾ ĐỘ CHỈNH SỬA X-Y (cho phôi ảnh khác) =====
const XY_KEYS = ["ho_ten", "ngay_sinh", "chuyen_nganh", "ma_sinh_vien", "thoi_han_the", "email"];

function fillXYFormFromConfig() {
  XY_KEYS.forEach(key => {
    const c = cardConfig[key];
    if (!c) return;
    const xEl = document.getElementById(`xy-${key}-x`);
    const yEl = document.getElementById(`xy-${key}-y`);
    const fontEl = document.getElementById(`xy-${key}-font`);
    if (xEl) xEl.value = c.x_ratio;
    if (yEl) yEl.value = c.y_ratio;
    if (fontEl) fontEl.value = c.font_size;
  });
}

function applyXYFormToConfig() {
  XY_KEYS.forEach(key => {
    const xEl = document.getElementById(`xy-${key}-x`);
    const yEl = document.getElementById(`xy-${key}-y`);
    const fontEl = document.getElementById(`xy-${key}-font`);
    if (!cardConfig[key]) cardConfig[key] = { bold: true, color: "#000000" };
    if (xEl && !isNaN(parseFloat(xEl.value))) cardConfig[key].x_ratio = parseFloat(xEl.value);
    if (yEl && !isNaN(parseFloat(yEl.value))) cardConfig[key].y_ratio = parseFloat(yEl.value);
    if (fontEl && !isNaN(parseInt(fontEl.value, 10))) cardConfig[key].font_size = Math.max(8, Math.min(48, parseInt(fontEl.value, 10)));
  });
  chrome.storage.local.set({ cardConfig }, () => {
    if (currentProfile) drawCard(currentProfile);
  });
}

function resetCardConfigToDefault() {
  cardConfig = JSON.parse(JSON.stringify(CARD_CONFIG_DEFAULT));
  chrome.storage.local.set({ cardConfig }, () => {
    fillXYFormFromConfig();
    if (currentProfile) drawCard(currentProfile);
  });
}

// ===== DOWNLOAD THẺ =====
function downloadCard() {
  const canvas = document.getElementById("cardCanvas");
  const link = document.createElement("a");
  link.download = `the-sinh-vien-${currentProfile.studentId}.png`;
  link.href = canvas.toDataURL("image/png");
  link.click();
}

// ===== GỬI PROFILE CHO CONTENT-SCRIPT =====
function fillFormAndSubmit() {
  if (!currentProfile) return;

  // Kiểm tra tab hiện tại: chỉ điền form khi đang ở trang SheerID
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs[0];
    const url = tab?.url || "";
    if (!url.includes("services.sheerid.com/verify")) {
      if (typeof alert !== "undefined") {
        alert("Mở trang xác minh SheerID (services.sheerid.com/verify/...) rồi bấm lại.\n\nHoặc dùng \"Mở trang test\" để thử tạo thẻ và tải ảnh.");
      }
      return;
    }

  const canvas = document.getElementById("cardCanvas");
  const imageData = canvas.toDataURL("image/png");

  // Lưu ảnh vào storage để content script có thể dùng ở bước upload sau này
  chrome.storage.local.set({ pendingUploadImage: imageData }, () => {
    console.log("Image saved for auto-upload.");

    chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
      const tab = tabs[0];
      if (!tab) return;

      // Hàm gửi message
      const sendMessage = () => {
        chrome.tabs.sendMessage(tab.id, {
          type: "FILL_SHEERID_AND_SUBMIT",
          profile: currentProfile
        }, response => {
          if (chrome.runtime.lastError) {
            console.log("Content script not ready, injecting now...");
            // Nếu lỗi (do content script chưa chạy), ta inject thủ công
            chrome.scripting.executeScript({
              target: { tabId: tab.id },
              files: ["content.js"]
            }, () => {
              if (chrome.runtime.lastError) {
                console.error("Injection failed: " + chrome.runtime.lastError.message);
                return;
              }
              setTimeout(() => {
                chrome.tabs.sendMessage(tab.id, {
                  type: "FILL_SHEERID_AND_SUBMIT",
                  profile: currentProfile
                });
              }, 500);
            });
          } else {
            console.log("Message sent successfully");
          }
        });
      };

      sendMessage();
    });
  });
  });
}

// ===== UI HELPERS =====
function updateButtonState(status) {
  const btn = document.getElementById("btn-verify");
  if (!btn) return;

  // Reset classes
  btn.classList.remove("btn-disabled", "btn-success", "btn-reviewing");
  btn.disabled = false;

  switch (status) {
    case "processing":
      btn.textContent = "Đang xử lý...";
      btn.classList.add("btn-disabled");
      btn.disabled = true;
      break;
    case "success":
      btn.textContent = "XÁC MINH THÀNH CÔNG";
      btn.classList.add("btn-success");
      btn.disabled = true; // Disabled
      break;
    case "reviewing":
      btn.textContent = "REVIEWING";
      btn.classList.add("btn-reviewing");
      btn.disabled = true; // Disabled
      break;
    case "error":
      // Báo lỗi nhưng vẫn cho bấm lại
      btn.textContent = "LỖI — THỬ LẠI";
      btn.disabled = false;
      break;
    default:
      btn.textContent = "XÁC MINH NGAY";
      break;
  }
}

// ===== KHỞI TẠO MÀN HÌNH CHÍNH (profile, cardConfig, UI) =====
function initMainView() {
  chrome.storage.local.get(["savedProfile", "verificationStatus", "cardConfig"], (data) => {
    if (data.cardConfig) {
      cardConfig = data.cardConfig;
      XY_KEYS.forEach(key => {
        if (!cardConfig[key]) cardConfig[key] = { ...CARD_CONFIG_DEFAULT[key] };
        if (cardConfig[key].bold === undefined) cardConfig[key].bold = true;
        if (!cardConfig[key].color) cardConfig[key].color = "#000000";
      });
    }
    if (data.savedProfile) {
      currentProfile = data.savedProfile;
      updatePopup(currentProfile);
    } else {
      currentProfile = generateRandomProfile();
      chrome.storage.local.set({ savedProfile: currentProfile });
      updatePopup(currentProfile);
    }
    updateButtonState(data.verificationStatus);
    fillXYFormFromConfig();
  });
}

function updateDebugBanner(show, isTestPage) {
  const banner = document.getElementById("debug-banner");
  const textEl = document.getElementById("debug-banner-text");
  if (!banner || !textEl) return;
  if (show) {
    banner.classList.remove("hidden");
    textEl.textContent = isTestPage
      ? "Trang test — Tạo thẻ, chỉnh X-Y, tải ảnh. Để xác minh thật, mở popup trên trang SheerID."
      : "Chế độ debug — Popup hiển thị trên mọi trang. Nút Xác minh chỉ hoạt động trên trang SheerID.";
  } else {
    banner.classList.add("hidden");
  }
}

// ===== MAIN =====
document.addEventListener("DOMContentLoaded", () => {
  // 1. Load debugMode rồi kiểm tra URL → quyết định hiển thị main hay error
  chrome.storage.local.get(["debugMode"], (dataStorage) => {
    const debugMode = !!dataStorage.debugMode;

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const currentTab = tabs[0];
      const url = currentTab?.url || "";
      const onSheerID = url.includes("services.sheerid.com/verify");
      const showMain = onSheerID || IS_TEST_PAGE || debugMode;

      if (showMain) {
        document.getElementById("main-view").classList.remove("hidden");
        document.getElementById("error-view").classList.add("hidden");
        initMainView();
        updateDebugBanner(IS_TEST_PAGE || (debugMode && !onSheerID), IS_TEST_PAGE);
        const cb = document.getElementById("checkbox-debug");
        if (cb) cb.checked = debugMode;
      } else {
        document.getElementById("main-view").classList.add("hidden");
        document.getElementById("error-view").classList.remove("hidden");
      }
    });
  });

  // Lắng nghe thay đổi storage để cập nhật UI real-time
  chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === "local" && changes.verificationStatus) {
      // Nếu status bị remove (undefined) hoặc null, reset về trạng thái ban đầu
      const newStatus = changes.verificationStatus.newValue || undefined;
      updateButtonState(newStatus);
    }
  });

  // Toggle xem chi tiết
  const btnToggle = document.getElementById("btn-toggle-details");
  const detailsContainer = document.getElementById("details-container");

  if (btnToggle && detailsContainer) {
    btnToggle.addEventListener("click", () => {
      const isHidden = detailsContainer.classList.contains("hidden");
      if (isHidden) {
        detailsContainer.classList.remove("hidden");
        btnToggle.textContent = "Ẩn chi tiết ▲";
      } else {
        detailsContainer.classList.add("hidden");
        btnToggle.textContent = "Xem chi tiết thẻ ▼";
      }
    });
  }

  // Nút XÁC MINH NGAY
  const btnVerify = document.getElementById("btn-verify");
  if (btnVerify) {
    btnVerify.addEventListener("click", () => {
      // Set status processing ngay lập tức
      chrome.storage.local.set({ verificationStatus: "processing" });
      updateButtonState("processing");
      fillFormAndSubmit();
    });
  }

  // Nút tạo lại thẻ
  const btnRegen = document.getElementById("btn-regenerate");
  if (btnRegen) {
    btnRegen.addEventListener("click", () => {
      currentProfile = generateRandomProfile();
      chrome.storage.local.set({ savedProfile: currentProfile });
      updatePopup(currentProfile);
    });
  }

  // Nút tải thẻ
  const btnDownload = document.getElementById("btn-download");
  if (btnDownload) {
    btnDownload.addEventListener("click", () => {
      downloadCard();
    });
  }

  // Chế độ chỉnh sửa X-Y (cho phôi ảnh khác)
  const btnToggleXY = document.getElementById("btn-toggle-xy");
  const xyEditContainer = document.getElementById("xy-edit-container");
  if (btnToggleXY && xyEditContainer) {
    btnToggleXY.addEventListener("click", () => {
      const isHidden = xyEditContainer.classList.contains("hidden");
      if (isHidden) {
        xyEditContainer.classList.remove("hidden");
        btnToggleXY.textContent = "Ẩn chỉnh sửa X-Y ▲";
        fillXYFormFromConfig();
      } else {
        xyEditContainer.classList.add("hidden");
        btnToggleXY.textContent = "Chỉnh sửa vị trí (X-Y) ▼";
      }
    });
  }
  const btnXYSave = document.getElementById("btn-xy-save");
  if (btnXYSave) btnXYSave.addEventListener("click", applyXYFormToConfig);
  const btnXYReset = document.getElementById("btn-xy-reset");
  if (btnXYReset) btnXYReset.addEventListener("click", resetCardConfigToDefault);

  // Debug: checkbox hiển thị trên mọi trang
  const checkboxDebug = document.getElementById("checkbox-debug");
  if (checkboxDebug) {
    checkboxDebug.addEventListener("change", () => {
      chrome.storage.local.set({ debugMode: checkboxDebug.checked });
    });
  }

  // Mở trang test (tab mới)
  function openTestPage() {
    chrome.tabs.create({ url: chrome.runtime.getURL("index.html") });
  }
  const btnOpenTest = document.getElementById("btn-open-test");
  if (btnOpenTest) btnOpenTest.addEventListener("click", openTestPage);
  const btnOpenTestPage = document.getElementById("btn-open-test-page");
  if (btnOpenTestPage) btnOpenTestPage.addEventListener("click", openTestPage);

  // Bật chế độ debug (từ màn hình lỗi)
  const btnEnableDebug = document.getElementById("btn-enable-debug");
  if (btnEnableDebug) {
    btnEnableDebug.addEventListener("click", () => {
      chrome.storage.local.set({ debugMode: true }, () => {
        document.getElementById("error-view").classList.add("hidden");
        document.getElementById("main-view").classList.remove("hidden");
        initMainView();
        updateDebugBanner(true, false);
        if (checkboxDebug) checkboxDebug.checked = true;
      });
    });
  }
});
