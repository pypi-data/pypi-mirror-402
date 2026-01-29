use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use tao::event_loop::EventLoopProxy;
use crate::events::CactusEvent;

/// A handle to send events to the main loop from other threads
#[pyclass]
pub struct CactusHandle {
    pub proxy: EventLoopProxy<CactusEvent>,
    pub memory_assets: Arc<Mutex<HashMap<String, (Vec<u8>, String)>>>,
}

#[pymethods]
impl CactusHandle {
    fn serve_data(&self, key: String, data: Vec<u8>, mime: String) {
        if let Ok(mut assets) = self.memory_assets.lock() {
            assets.insert(key, (data, mime));
        }
    }

    fn close_splash(&self) {
        let _ = self.proxy.send_event(CactusEvent::CloseSplash);
    }

    fn eval(&self, script: String) {
        let _ = self.proxy.send_event(CactusEvent::Eval(script));
    }

    fn start_drag(&self) {
        let _ = self.proxy.send_event(CactusEvent::Drag);
    }

    fn minimize(&self) {
        let _ = self.proxy.send_event(CactusEvent::Minimize);
    }

    fn maximize(&self) {
        let _ = self.proxy.send_event(CactusEvent::Maximize);
    }

    fn restore(&self) {
        let _ = self.proxy.send_event(CactusEvent::Restore);
    }

    fn close(&self) {
        let _ = self.proxy.send_event(CactusEvent::Close);
    }

    fn set_title(&self, title: String) {
        let _ = self.proxy.send_event(CactusEvent::SetTitle(title));
    }

    fn set_menu(&self, menu_json: String) {
        let _ = self.proxy.send_event(CactusEvent::SetMenu(menu_json));
    }

    fn register_shortcut(&self, accelerator: String, id: u32) {
        let _ = self.proxy.send_event(CactusEvent::RegisterShortcut(accelerator, id));
    }

    #[pyo3(signature = (tray_json, icon_path=None))]
    fn set_tray(&self, tray_json: String, icon_path: Option<String>) {
        let _ = self.proxy.send_event(CactusEvent::SetTray(tray_json, icon_path));
    }

    fn set_window_icon(&self, path: String) {
        let _ = self.proxy.send_event(CactusEvent::SetWindowIcon(path));
    }

    // --- Synchronous Dialogs (Blocking Python Thread) ---

    fn message_box(&self, title: String, message: String) {
        rfd::MessageDialog::new()
            .set_title(&title)
            .set_description(&message)
            .set_level(rfd::MessageLevel::Info)
            .show();
    }

    #[pyo3(signature = (title, default_path=None))]
    fn open_file_dialog(&self, title: String, default_path: Option<String>) -> Option<String> {
        let mut dialog = rfd::FileDialog::new().set_title(&title);
        if let Some(path) = default_path {
            dialog = dialog.set_directory(path);
        }
        dialog.pick_file().map(|p| p.to_string_lossy().to_string())
    }

    #[pyo3(signature = (title, default_path=None))]
    fn save_file_dialog(&self, title: String, default_path: Option<String>) -> Option<String> {
        let mut dialog = rfd::FileDialog::new().set_title(&title);
        if let Some(path) = default_path {
            dialog = dialog.set_directory(path);
        }
        dialog.save_file().map(|p| p.to_string_lossy().to_string())
    }

    #[pyo3(signature = (title, default_path=None))]
    fn select_folder_dialog(&self, title: String, default_path: Option<String>) -> Option<String> {
        let mut dialog = rfd::FileDialog::new().set_title(&title);
        if let Some(path) = default_path {
            dialog = dialog.set_directory(path);
        }
        dialog.pick_folder().map(|p| p.to_string_lossy().to_string())
    }

    #[pyo3(signature = (title, message, icon_path=None))]
    fn system_notification(&self, title: String, message: String, icon_path: Option<String>) {
        let _ = self.proxy.send_event(CactusEvent::Notification(title, message, icon_path));
    }

    fn set_taskbar_progress(&self, state: String, progress: u32) {
        let _ = self.proxy.send_event(CactusEvent::SetTaskbarProgress(state, progress));
    }

    fn set_app_id(&self, app_id: String) {
        let _ = self.proxy.send_event(CactusEvent::SetAppId(app_id));
    }

    fn set_fullscreen(&self, fullscreen: bool) {
        let _ = self.proxy.send_event(CactusEvent::SetFullscreen(fullscreen));
    }

    fn set_resizable(&self, resizable: bool) {
        let _ = self.proxy.send_event(CactusEvent::SetResizable(resizable));
    }

    fn set_always_on_top(&self, always_on_top: bool) {
        let _ = self.proxy.send_event(CactusEvent::SetAlwaysOnTop(always_on_top));
    }

    fn hide(&self) {
        let _ = self.proxy.send_event(CactusEvent::Hide);
    }

    fn show(&self) {
        let _ = self.proxy.send_event(CactusEvent::Show);
    }
}
