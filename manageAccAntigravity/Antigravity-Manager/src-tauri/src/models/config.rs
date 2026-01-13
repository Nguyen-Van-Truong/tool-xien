use serde::{Deserialize, Serialize};
use crate::proxy::ProxyConfig;

/// 应用配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub language: String,
    pub theme: String,
    pub auto_refresh: bool,
    pub refresh_interval: i32,  // 分钟
    pub auto_sync: bool,
    pub sync_interval: i32,  // 分钟
    pub default_export_path: Option<String>,
    #[serde(default)]
    pub proxy: ProxyConfig,
    pub antigravity_executable: Option<String>, // [NEW] 手动指定的反重力程序路径
    pub antigravity_args: Option<Vec<String>>, // [NEW] Antigravity 启动参数
    #[serde(default)]
    pub auto_launch: bool,  // 开机自动启动
}

impl AppConfig {
    pub fn new() -> Self {
        Self {
            language: "zh".to_string(),
            theme: "system".to_string(),
            auto_refresh: false,
            refresh_interval: 15,
            auto_sync: false,
            sync_interval: 5,
            default_export_path: None,
            proxy: ProxyConfig::default(),
            antigravity_executable: None,
            antigravity_args: None,
            auto_launch: false,
        }
    }
}

impl Default for AppConfig {
    fn default() -> Self {
        Self::new()
    }
}
