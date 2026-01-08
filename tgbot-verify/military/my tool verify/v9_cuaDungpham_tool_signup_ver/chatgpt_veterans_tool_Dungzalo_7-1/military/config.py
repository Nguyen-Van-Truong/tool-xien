# Military SheerID Verification Configuration
# Based on ThanhNguyxn/SheerID-Verification-Tool

# SheerID API Configuration
SHEERID_BASE_URL = 'https://services.sheerid.com'
SHEERID_API = 'https://services.sheerid.com/rest/v2'
MY_SHEERID_URL = 'https://my.sheerid.com'

# ChatGPT Veterans Program ID
PROGRAM_ID = '690415d58971e73ca187d8c9'

# File Size Limit
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB

# Military Status Options
MILITARY_STATUS = ['VETERAN', 'ACTIVE_DUTY', 'RESERVIST']

# User Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"

# Military Branch Organization IDs (from ThanhNguyxn repo)
BRANCH_ORG_MAP = {
    "Army": {"id": 4070, "name": "Army"},
    "Air Force": {"id": 4073, "name": "Air Force"},
    "Navy": {"id": 4072, "name": "Navy"},
    "Marine Corps": {"id": 4071, "name": "Marine Corps"},
    "Coast Guard": {"id": 4074, "name": "Coast Guard"},
    "Space Force": {"id": 4544268, "name": "Space Force"},
    "Army National Guard": {"id": 4075, "name": "Army National Guard"},
    "Army Reserve": {"id": 4076, "name": "Army Reserve"},
    "Air National Guard": {"id": 4079, "name": "Air National Guard"},
    "Air Force Reserve": {"id": 4080, "name": "Air Force Reserve"},
    "Navy Reserve": {"id": 4078, "name": "Navy Reserve"},
    "Marine Corps Reserve": {"id": 4077, "name": "Marine Corps Forces Reserve"},
    "Coast Guard Reserve": {"id": 4081, "name": "Coast Guard Reserve"},
}

# Military Organizations (legacy format for compatibility)
ORGANIZATIONS = {
    '4070': {
        'id': 4070,
        'idExtended': '4070',
        'name': 'Army',
        'country': 'US',
        'type': 'MILITARY'
    },
    '4073': {
        'id': 4073,
        'idExtended': '4073',
        'name': 'Air Force',
        'country': 'US',
        'type': 'MILITARY'
    },
    '4072': {
        'id': 4072,
        'idExtended': '4072',
        'name': 'Navy',
        'country': 'US',
        'type': 'MILITARY'
    },
    '4071': {
        'id': 4071,
        'idExtended': '4071',
        'name': 'Marine Corps',
        'country': 'US',
        'type': 'MILITARY'
    },
    '4074': {
        'id': 4074,
        'idExtended': '4074',
        'name': 'Coast Guard',
        'country': 'US',
        'type': 'MILITARY'
    },
    '4544268': {
        'id': 4544268,
        'idExtended': '4544268',
        'name': 'Space Force',
        'country': 'US',
        'type': 'MILITARY'
    },
    '4075': {
        'id': 4075,
        'idExtended': '4075',
        'name': 'Army National Guard',
        'country': 'US',
        'type': 'MILITARY'
    },
    '4076': {
        'id': 4076,
        'idExtended': '4076',
        'name': 'Army Reserve',
        'country': 'US',
        'type': 'MILITARY'
    },
    '4079': {
        'id': 4079,
        'idExtended': '4079',
        'name': 'Air National Guard',
        'country': 'US',
        'type': 'MILITARY'
    },
    '4080': {
        'id': 4080,
        'idExtended': '4080',
        'name': 'Air Force Reserve',
        'country': 'US',
        'type': 'MILITARY'
    },
    '4078': {
        'id': 4078,
        'idExtended': '4078',
        'name': 'Navy Reserve',
        'country': 'US',
        'type': 'MILITARY'
    },
    '4077': {
        'id': 4077,
        'idExtended': '4077',
        'name': 'Marine Corps Forces Reserve',
        'country': 'US',
        'type': 'MILITARY'
    },
    '4081': {
        'id': 4081,
        'idExtended': '4081',
        'name': 'Coast Guard Reserve',
        'country': 'US',
        'type': 'MILITARY'
    }
}

# Default Organization
DEFAULT_ORG_ID = '4070'  # Army

# Default branch for random selection (main branches only for better success rate)
MAIN_BRANCHES = ['Army', 'Air Force', 'Navy', 'Marine Corps', 'Coast Guard']
