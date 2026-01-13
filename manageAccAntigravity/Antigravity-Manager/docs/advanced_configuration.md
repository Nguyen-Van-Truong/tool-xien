# 高级配置与实验性功能 (Advanced Configuration)

Antigravity v3.3.16 引入了 `ExperimentalConfig`，这是一组默认开启的实验性功能开关，旨在提升系统的鲁棒性与兼容性。这些配置位于 `src-tauri/src/proxy/config.rs` 中，目前暂未暴露到 UI 界面。

## 功能列表

### 1. 双层签名缓存 (Signature Cache)
*   **配置项**: `enable_signature_cache`
*   **默认值**: `true`
*   **说明**: 启用后，系统会缓存 `ToolUse ID` 与 `Thought Signature` 的映射关系。
*   **作用**: 解决部分客户端（如 Claude Desktop CLI, Cherry Studio）在多轮对话中可能丢失历史 Tool Call 签名的问题。当上游 API 报错 "Missing signature" 时，系统可从缓存中自动恢复，避免对话中断。

### 2. 工具循环自动恢复 (Tool Loop Recovery)
*   **配置项**: `enable_tool_loop_recovery`
*   **默认值**: `true`
*   **说明**: 启用后，系统会实时监控对话状态，检测“死循环”模式。
*   **触发条件**: 检测到连续的 `ToolUse` -> `ToolResult` 循环，且 `Assistant` 消息中缺少 `Thinking` 块（通常因签名校验失败被 stripping）。
*   **行为**: 自动注入合成消息（`Assistant: Tool execution completed.` -> `User: Proceed.`）来打破死循环，强制模型进入下一轮思考。

### 3. 跨模型兼容性检查 (Cross-Model Checks)
*   **配置项**: `enable_cross_model_checks`
*   **默认值**: `true`
*   **说明**: 防止在同一会话中切换不同系列模型（如 Claude -> Gemini）时引发的签名错误。
*   **作用**: 当检测到历史消息中的签名属于不兼容的模型家族（如 `claude-3-5` vs `gemini-2.0`）时，系统会自动丢弃旧签名，防止 API 拒绝请求。

## 自定义配置

目前这些配置项可通过修改 `src-tauri/src/proxy/config.rs` 中的 `default_true` 默认值来调整，或者等待未来版本集成到 "Settings -> Advanced" 界面。

```rust
// src-tauri/src/proxy/config.rs

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExperimentalConfig {
    #[serde(default = "default_true")]
    pub enable_signature_cache: bool,
    // ...
}
```
