# ChatGPT Military SheerID Verification Guide

## 📋 Overview

ChatGPT Military verification process differs from regular student/teacher verification. It requires calling an additional API to collect military status information before submitting the personal information form.

## 🔄 Verification Flow

### Step 1: Collect Military Status (collectMilitaryStatus)

Before submitting the personal information form, you must first call this API to set the military status.

**Request Information**:
- **URL**: `https://services.sheerid.com/rest/v2/verification/{verificationId}/step/collectMilitaryStatus`
- **Method**: `POST`
- **Parameters**:
```json
{
    "status": "VETERAN" // 3 options available
}
```

**Response Example**:
```json
{
    "verificationId": "{verification_id}",
    "currentStep": "collectInactiveMilitaryPersonalInfo",
    "errorIds": [],
    "segment": "military",
    "subSegment": "veteran",
    "locale": "en-US",
    "country": null,
    "created": 1766539517800,
    "updated": 1766540141435,
    "submissionUrl": "https://services.sheerid.com/rest/v2/verification/{verification_id}/step/collectInactiveMilitaryPersonalInfo",
    "instantMatchAttempts": 0
}
```

**Key Fields**:
- `submissionUrl`: The submission URL to use in the next step
- `currentStep`: Current step, should change to `collectInactiveMilitaryPersonalInfo`

---

### Step 2: Collect Inactive Military Personal Info (collectInactiveMilitaryPersonalInfo)

Use the `submissionUrl` returned from Step 1 to submit personal information.

**Request Information**:
- **URL**: Get from Step 1 response `submissionUrl`
  - Example: `https://services.sheerid.com/rest/v2/verification/{verificationId}/step/collectInactiveMilitaryPersonalInfo`
- **Method**: `POST`
- **Parameters**:
```json
{
    "firstName": "name",
    "lastName": "name",
    "birthDate": "1939-12-01",
    "email": "your mail",
    "phoneNumber": "",
    "organization": {
        "id": 4070,
        "name": "Army"
    },
    "dischargeDate": "2025-05-29",
    "locale": "en-US",
    "country": "US",
    "metadata": {
        "marketConsentValue": false,
        "refererUrl": "",
        "verificationId": "",
        "flags": "{\"doc-upload-considerations\":\"default\",\"doc-upload-may24\":\"default\",\"doc-upload-redesign-use-legacy-message-keys\":false,\"docUpload-assertion-checklist\":\"default\",\"include-cvec-field-france-student\":\"not-labeled-optional\",\"org-search-overlay\":\"default\",\"org-selected-display\":\"default\"}",
        "submissionOptIn": "By submitting the personal information above, I acknowledge that my personal information is being collected under the <a target=\"_blank\" rel=\"noopener noreferrer\" class=\"sid-privacy-policy sid-link\" href=\"https://openai.com/policies/privacy-policy/\">privacy policy</a> of the business from which I am seeking a discount, and I understand that my personal information will be shared with SheerID as a processor/third-party service provider in order for SheerID to confirm my eligibility for a special offer. Contact OpenAI Support for further assistance at support@openai.com"
    }
}
```

**Key Field Descriptions**:
- `firstName`: First name
- `lastName`: Last name
- `birthDate`: Date of birth, format `YYYY-MM-DD`
- `email`: Email address
- `phoneNumber`: Phone number (can be empty)
- `organization`: Military organization info (see organization list below)
- `dischargeDate`: Discharge date, format `YYYY-MM-DD`
- `locale`: Locale, default `en-US`
- `country`: Country code, default `US`
- `metadata`: Metadata information (includes privacy policy consent text, etc.)

---

## 🎖️ Military Organization List

Available military organization options:

```json
[
    {
        "id": 4070,
        "idExtended": "4070",
        "name": "Army",
        "country": "US",
        "type": "MILITARY",
        "latitude": 39.7837304,
        "longitude": -100.445882
    },
    {
        "id": 4073,
        "idExtended": "4073",
        "name": "Air Force",
        "country": "US",
        "type": "MILITARY",
        "latitude": 39.7837304,
        "longitude": -100.445882
    },
    {
        "id": 4072,
        "idExtended": "4072",
        "name": "Navy",
        "country": "US",
        "type": "MILITARY",
        "latitude": 39.7837304,
        "longitude": -100.445882
    },
    {
        "id": 4071,
        "idExtended": "4071",
        "name": "Marine Corps",
        "country": "US",
        "type": "MILITARY",
        "latitude": 39.7837304,
        "longitude": -100.445882
    },
    {
        "id": 4074,
        "idExtended": "4074",
        "name": "Coast Guard",
        "country": "US",
        "type": "MILITARY",
        "latitude": 39.7837304,
        "longitude": -100.445882
    },
    {
        "id": 4544268,
        "idExtended": "4544268",
        "name": "Space Force",
        "country": "US",
        "type": "MILITARY",
        "latitude": 39.7837304,
        "longitude": -100.445882
    }
]
```

**Organization ID Mapping**:
- `4070` - Army
- `4073` - Air Force
- `4072` - Navy
- `4071` - Marine Corps
- `4074` - Coast Guard
- `4544268` - Space Force

---

## 🔑 Implementation Notes

1. **Must Execute in Order**: You must first call `collectMilitaryStatus`, get the `submissionUrl`, then call `collectInactiveMilitaryPersonalInfo`
2. **Organization Info**: The `organization` field needs to include `id` and `name`, can be randomly selected from the list above or let user choose
3. **Date Format**: `birthDate` and `dischargeDate` must use `YYYY-MM-DD` format
4. **Metadata**: The `submissionOptIn` in `metadata` field contains privacy policy consent text, needs to be extracted from original request or constructed

---

## 📝 Implementation Status

- [x] Implement `collectMilitaryStatus` API call
- [x] Implement `collectInactiveMilitaryPersonalInfo` API call
- [x] Add military organization selection logic
- [x] Generate required personal information (name, birth date, email, etc.)
- [x] Generate discharge date (reasonable time range)
- [x] Handle metadata information
- [x] Integrate into main bot command system (`/verify6`)

