"""Military Verification Configuration"""

# SheerID API Configuration
SHEERID_BASE_URL = "https://services.sheerid.com"

# ChatGPT Military Program ID (cần cập nhật định kỳ)
PROGRAM_ID = "67576f01ab178a6eb556f64d"

# Military Status Options
MILITARY_STATUSES = {
    "VETERAN": "Cựu chiến binh (đã xuất ngũ)",
    "ACTIVE_DUTY": "Đang tại ngũ", 
    "MILITARY_FAMILY": "Gia đình quân nhân"
}

# Military Branch Organizations
ORGANIZATIONS = [
    {"id": 4070, "name": "Army", "name_vi": "Lục quân"},
    {"id": 4073, "name": "Air Force", "name_vi": "Không quân"},
    {"id": 4072, "name": "Navy", "name_vi": "Hải quân"},
    {"id": 4071, "name": "Marine Corps", "name_vi": "Thủy quân lục chiến"},
    {"id": 4074, "name": "Coast Guard", "name_vi": "Tuần duyên"},
    {"id": 4544268, "name": "Space Force", "name_vi": "Lực lượng Vũ trụ"},
]

# Email domains for random generation
EMAIL_DOMAINS = [
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "aol.com", "icloud.com", "mail.com", "protonmail.com"
]

# VLM Scraper Configuration
VLM_BASE_URL = "https://www.vlm.cem.va.gov"
VLM_SEARCH_URL = "https://www.vlm.cem.va.gov"

# Default search parameters
DEFAULT_DEATH_YEAR = 2025
DEFAULT_BRANCHES = ["Navy", "Army", "Air Force", "Marine Corps", "Coast Guard"]
