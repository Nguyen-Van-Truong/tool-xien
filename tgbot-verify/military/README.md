# ChatGPT 军人 SheerID 认证思路

## 📋 概述

ChatGPT 军人认证流程与普通学生/教师认证不同，需要先执行一个额外的接口来收集军人状态信息，然后再提交个人信息表单。

## 🔄 认证流程

### 第一步：收集军人状态 (collectMilitaryStatus)

在提交个人信息表单之前，必须先调用此接口来设置军人状态。

**请求信息**：
- **URL**: `https://services.sheerid.com/rest/v2/verification/{verificationId}/step/collectMilitaryStatus`
- **方法**: `POST`
- **参数**:
```json
{
    "status": "VETERAN" // 总共3个
}
```

**响应示例**：
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

**关键字段**：
- `submissionUrl`: 下一步需要使用的提交URL
- `currentStep`: 当前步骤，应该变为 `collectInactiveMilitaryPersonalInfo`

---

### 第二步：收集非现役军人个人信息 (collectInactiveMilitaryPersonalInfo)

使用第一步返回的 `submissionUrl` 提交个人信息。

**请求信息**：
- **URL**: 从第一步响应的 `submissionUrl` 获取
  - 例如: `https://services.sheerid.com/rest/v2/verification/{verificationId}/step/collectInactiveMilitaryPersonalInfo`
- **方法**: `POST`
- **参数**:
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

**关键字段说明**：
- `firstName`: 名字
- `lastName`: 姓氏
- `birthDate`: 出生日期，格式 `YYYY-MM-DD`
- `email`: 邮箱地址
- `phoneNumber`: 电话号码（可为空）
- `organization`: 军队组织信息（见下方组织列表）
- `dischargeDate`: 退役日期，格式 `YYYY-MM-DD`
- `locale`: 语言区域，默认 `en-US`
- `country`: 国家代码，默认 `US`
- `metadata`: 元数据信息（包含隐私政策同意文本等）

---

## 🎖️ 军队组织列表 (Organization)

以下是可用的军队组织选项：

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

**组织ID映射**：
- `4070` - Army (陆军)
- `4073` - Air Force (空军)
- `4072` - Navy (海军)
- `4071` - Marine Corps (海军陆战队)
- `4074` - Coast Guard (海岸警卫队)
- `4544268` - Space Force (太空军)

---

## 🔑 实现要点

1. **必须按顺序执行**：必须先调用 `collectMilitaryStatus`，获取 `submissionUrl` 后，再调用 `collectInactiveMilitaryPersonalInfo`
2. **组织信息**：`organization` 字段需要包含 `id` 和 `name`，可以从上述列表中随机选择或让用户选择
3. **日期格式**：`birthDate` 和 `dischargeDate` 必须使用 `YYYY-MM-DD` 格式
4. **元数据**：`metadata` 字段中的 `submissionOptIn` 包含隐私政策同意文本，需要从原始请求中提取或构造

---

## 📝 待实现功能

- [ ] 实现 `collectMilitaryStatus` 接口调用
- [ ] 实现 `collectInactiveMilitaryPersonalInfo` 接口调用
- [ ] 添加军队组织选择逻辑
- [ ] 生成符合要求的个人信息（姓名、出生日期、邮箱等）
- [ ] 生成退役日期（需要合理的时间范围）
- [ ] 处理元数据信息（从原始请求中提取或构造）
- [ ] 集成到主机器人命令系统（如 `/verify6`）

