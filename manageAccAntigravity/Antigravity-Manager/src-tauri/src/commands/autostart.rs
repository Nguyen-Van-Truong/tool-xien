// Autostart 命令
use tauri_plugin_autostart::ManagerExt;

#[tauri::command]
pub async fn toggle_auto_launch(
    app: tauri::AppHandle,
    enable: bool,
) -> Result<(), String> {
    let manager = app.autolaunch();
    
    if enable {
        manager.enable().map_err(|e| e.to_string())?;
        crate::modules::logger::log_info("已启用开机自动启动");
    } else {
        manager.disable().map_err(|e| e.to_string())?;
        crate::modules::logger::log_info("已禁用开机自动启动");
    }
    
    Ok(())
}

#[tauri::command]
pub async fn is_auto_launch_enabled(app: tauri::AppHandle) -> Result<bool, String> {
    let manager = app.autolaunch();
    manager.is_enabled().map_err(|e| e.to_string())
}
