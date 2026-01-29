use pyo3::prelude::*;
use std::borrow::Cow;
use std::fs;
use std::path::PathBuf;
use tao::{
    event::{Event, StartCause, WindowEvent},
    event_loop::{ControlFlow, EventLoopBuilder},
    window::{WindowBuilder},
};
use wry::http::{Response, header};
use wry::{WebViewBuilder, DragDropEvent};

use std::collections::HashMap;
use std::sync::{Arc, Mutex};

use muda::{Menu, Submenu, MenuEvent};
use tray_icon::{TrayIconBuilder, TrayIcon, Icon as TrayIconType};
use global_hotkey::{GlobalHotKeyManager, hotkey::HotKey, GlobalHotKeyEvent};

#[cfg(target_os = "windows")]
use tao::platform::windows::WindowExtWindows;

use crate::events::CactusEvent;
use crate::handle::CactusHandle;
use crate::menu::{MenuSchema, build_menu_recursive};
use crate::utils::{load_icon_tao, load_icon_tray};

#[pyfunction]
#[pyo3(signature = (
    title, 
    url, 
    on_app_ready, 
    ipc_callback, 
    asset_root=None, 
    initialization_script=None,
    frameless=false,
    resizable=true,
    always_on_top=false,
    maximized=false,
    transparent=false,
    splash_html=None,
    splash_width=400,
    splash_height=300,
    fullscreen=false
))]
pub fn start_engine(
    py: Python<'_>, 
    title: String, 
    url: String, 
    on_app_ready: PyObject,
    ipc_callback: PyObject, 
    asset_root: Option<String>,
    initialization_script: Option<String>,
    frameless: bool,
    resizable: bool,
    always_on_top: bool,
    maximized: bool,
    transparent: bool,
    splash_html: Option<String>,
    splash_width: u32,
    splash_height: u32,
    fullscreen: bool
) -> PyResult<()> {
    
    // 1. Clone callbacks
    let ipc_cb = ipc_callback.clone_ref(py);
    let ready_cb = on_app_ready.clone_ref(py);
    let ipc_cb_for_loop = ipc_callback.clone_ref(py);

    // 2. Prepare asset root
    let root = asset_root.map(PathBuf::from);
    let memory_assets: Arc<Mutex<HashMap<String, (Vec<u8>, String)>>> = Arc::new(Mutex::new(HashMap::new()));

    // 3. Create Event Loop with Custom Event
    let event_loop = EventLoopBuilder::<CactusEvent>::with_user_event().build();
    let proxy = event_loop.create_proxy();

    // 4. Create Main Window (Hidden if splash is active)
    let mut window_builder = WindowBuilder::new()
        .with_title(title)
        .with_resizable(resizable)
        .with_always_on_top(always_on_top)
        .with_maximized(maximized)
        .with_transparent(transparent)
        .with_visible(splash_html.is_none());
    
    if fullscreen {
        window_builder = window_builder.with_fullscreen(Some(tao::window::Fullscreen::Borderless(None)));
    }
    
    if frameless {
        window_builder = window_builder.with_decorations(false);
    }

    let window = window_builder.build(&event_loop)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    // --- Create Splash Window if requested ---
    let mut splash_window = None;
    let mut _splash_webview = None;

    if let Some(html) = splash_html {
        let sw = WindowBuilder::new()
            .with_title("Loading...")
            .with_decorations(false)
            .with_resizable(false)
            .with_always_on_top(true)
            .with_inner_size(tao::dpi::LogicalSize::new(splash_width, splash_height))
            .build(&event_loop)
            .unwrap();
        
        // Center splash window
        if let Some(monitor) = sw.current_monitor() {
            let monitor_size = monitor.size();
            let window_size = sw.outer_size();
            let x = (monitor_size.width as i32 - window_size.width as i32) / 2;
            let y = (monitor_size.height as i32 - window_size.height as i32) / 2;
            sw.set_outer_position(tao::dpi::PhysicalPosition::new(x, y));
        }

        let swv = WebViewBuilder::new(&sw)
            .with_html(html)
            .build()
            .unwrap();
        
        splash_window = Some(sw);
        _splash_webview = Some(swv);
    }

    let hotkey_manager = GlobalHotKeyManager::new().unwrap();
    let mut _system_tray: Option<TrayIcon> = None;
    let mut _window_menu: Option<Menu> = None;
    let mut hotkeys: std::collections::HashMap<u32, HotKey> = std::collections::HashMap::new();

    // 5. Configure WebView
    let mut builder = WebViewBuilder::new(&window)
        .with_url(url.as_str())
        .with_devtools(true);
    
    if let Some(script) = initialization_script {
        builder = builder.with_initialization_script(&script);
    }
    
    let ipc_cb_for_drop = ipc_callback.clone_ref(py);
    
    builder = builder.with_ipc_handler(move |request| {
            let msg = request.body().clone(); 
            Python::with_gil(|py| {
                let args = (msg,);
                if let Err(e) = ipc_cb.call1(py, args) {
                    e.print_and_set_sys_last_vars(py);
                }
            });
        })
        .with_drag_drop_handler(move |event| {
            match event {
                DragDropEvent::Drop { paths, .. } => {
                    let paths_str: Vec<String> = paths.iter().map(|p| p.to_string_lossy().to_string()).collect();
                    Python::with_gil(|py| {
                         if let Ok(json) = serde_json::to_string(&serde_json::json!({
                            "event": "native_drop",
                            "paths": paths_str
                         })) {
                             let _ = ipc_cb_for_drop.call1(py, (json,));
                         }
                    });
                }
                _ => {}
            }
            true
        });

    // 6. Register Custom Protocol (Renamed to 'ccat')
    let mem_assets_protocol = memory_assets.clone();    
    builder = builder.with_custom_protocol("ccat".to_string(), move |request| {
             let uri = request.uri();
             
             let host = uri.host().unwrap_or("");
             let path = uri.path().to_string();
             
             let mut clean_path = if host == "localhost" || host == "app" || host == "" {
                 path
             } else {
                 format!("{}{}", host, path)
             };
             
             while clean_path.starts_with('/') {
                 clean_path.remove(0);
             }

             // Normalize slashes for consistency
             let clean_path = clean_path.replace('/', std::path::MAIN_SEPARATOR_STR);

             // Check Memory Assets First
             if clean_path.starts_with("data/") {
                let key = &clean_path[5..];
                if let Ok(assets) = mem_assets_protocol.lock() {
                    if let Some((content, mime)) = assets.get(key) {
                        return Response::builder()
                            .header(header::CONTENT_TYPE, mime)
                            .header(header::ACCESS_CONTROL_ALLOW_ORIGIN, "*")
                            .body(Cow::from(content.clone()))
                            .unwrap();
                    }
                }
             }

             // Fallback to disk if not in memory
             let mut full_path = if let Some(ref p) = root {
                 let candidate = p.join(&clean_path);
                 if candidate.exists() {
                     candidate
                 } else {
                     PathBuf::from(&clean_path)
                 }
             } else {
                 PathBuf::from(&clean_path)
             };

             // If the path ends with a slash but is not a directory, try stripping it
             // This handles ccat://index.html/ being parsed as host=index.html path=/
             if clean_path.ends_with('/') && !full_path.is_dir() {
                 let stripped = clean_path.trim_end_matches('/');
                 let mut alt_path = if let Some(ref p) = root {
                     let candidate = p.join(stripped);
                     if candidate.exists() { candidate } else { PathBuf::from(stripped) }
                 } else {
                     PathBuf::from(stripped)
                 };
                 if alt_path.exists() && !alt_path.is_dir() {
                     full_path = alt_path;
                 }
             }

             if full_path.is_dir() {
                 full_path = full_path.join("index.html");
             }
             
             let mime = if full_path.extension().and_then(|s| s.to_str()) == Some("html") { "text/html" }
                        else if full_path.extension().and_then(|s| s.to_str()) == Some("js") { "text/javascript" }
                        else if full_path.extension().and_then(|s| s.to_str()) == Some("mjs") { "text/javascript" }
                        else if full_path.extension().and_then(|s| s.to_str()) == Some("css") { "text/css" }
                        else if full_path.extension().and_then(|s| s.to_str()) == Some("png") { "image/png" }
                        else if full_path.extension().and_then(|s| s.to_str()) == Some("jpg") || full_path.extension().and_then(|s| s.to_str()) == Some("jpeg") { "image/jpeg" }
                        else if full_path.extension().and_then(|s| s.to_str()) == Some("gif") { "image/gif" }
                        else if full_path.extension().and_then(|s| s.to_str()) == Some("svg") { "image/svg+xml" }
                        else if full_path.extension().and_then(|s| s.to_str()) == Some("ico") { "image/x-icon" }
                        else if full_path.extension().and_then(|s| s.to_str()) == Some("json") { "application/json" }
                        else if full_path.extension().and_then(|s| s.to_str()) == Some("woff") { "font/woff" }
                        else if full_path.extension().and_then(|s| s.to_str()) == Some("woff2") { "font/woff2" }
                        else if full_path.extension().and_then(|s| s.to_str()) == Some("ttf") { "font/ttf" }
                        else { "application/octet-stream" };

             match fs::read(&full_path) {
                 Ok(content) => {
                     Response::builder()
                        .header(header::CONTENT_TYPE, mime)
                        .header(header::ACCESS_CONTROL_ALLOW_ORIGIN, "*")
                        .header(header::ACCESS_CONTROL_ALLOW_METHODS, "GET, POST, PUT, DELETE, OPTIONS")
                        .header(header::ACCESS_CONTROL_ALLOW_HEADERS, "*")
                        .body(Cow::from(content))
                        .unwrap()
                 },
                 Err(e) => {
                     eprintln!("[CactusCat] 404: {} | Error: {}", full_path.display(), e);
                     Response::builder()
                        .status(404)
                        .header(header::ACCESS_CONTROL_ALLOW_ORIGIN, "*")
                        .body(Cow::from(format!("Not Found: {}", full_path.display()).as_bytes().to_vec()))
                        .unwrap()
                 }
             }
        });

    let webview = builder.build()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    // 7. Notify Python that we are ready
    let handle = CactusHandle { 
        proxy,
        memory_assets: memory_assets.clone()
    };
    if let Err(e) = ready_cb.call1(py, (handle,)) {
        e.print_and_set_sys_last_vars(py);
    }

    // 8. Run the loop
    event_loop.run(move |event, _, control_flow| {
        *control_flow = ControlFlow::Wait;

        match event {
            Event::NewEvents(StartCause::Init) => println!("CactusCat Engine Started! 🌵🐱"),
            Event::WindowEvent {
                event: WindowEvent::CloseRequested,
                ..
            } => {
                Python::with_gil(|py| {
                    if let Ok(json) = serde_json::to_string(&serde_json::json!({
                        "event": "window_close"
                    })) {
                        let _ = ipc_cb_for_loop.call1(py, (json,));
                    }
                });
                *control_flow = ControlFlow::Exit;
            }
            Event::UserEvent(event) => match event {
                CactusEvent::Eval(script) => {
                    let _ = webview.evaluate_script(&script);
                }
                CactusEvent::Minimize => {
                    window.set_minimized(true);
                }
                CactusEvent::Maximize => {
                    let is_max = window.is_maximized();
                    window.set_maximized(!is_max);
                }
                CactusEvent::Restore => {
                    window.set_minimized(false);
                }
                CactusEvent::Close => {
                    *control_flow = ControlFlow::Exit;
                }
                CactusEvent::SetTitle(title) => {
                    window.set_title(&title);
                }
                CactusEvent::SetMenu(json) => {
                    if let Ok(menus) = serde_json::from_str::<Vec<MenuSchema>>(&json) {
                        let menu = Menu::new();
                        for m in menus {
                            let submenu = Submenu::new(&m.title, true);
                            let children = build_menu_recursive(m.items);
                            for child in children {
                                submenu.append(child.as_ref()).unwrap();
                            }
                            menu.append(&submenu).unwrap();
                        }
                        
                        #[cfg(target_os = "windows")]
                        unsafe { menu.init_for_hwnd(window.hwnd() as _) }.unwrap();
                         #[cfg(target_os = "macos")]
                        menu.init_for_nsapp();

                        _window_menu = Some(menu);
                    }
                }
                CactusEvent::SetTray(json, icon_path) => {
                    if let Ok(config) = serde_json::from_str::<MenuSchema>(&json) {
                         let tray_menu = Menu::new();
                         let children = build_menu_recursive(config.items);
                         for child in children {
                             tray_menu.append(child.as_ref()).unwrap();
                         }
                         
                         let icon = icon_path.and_then(|p| load_icon_tray(&p))
                             .unwrap_or_else(|| {
                                 TrayIconType::from_rgba(vec![0; 32 * 32 * 4], 32, 32).unwrap()
                             });

                         _system_tray = Some(
                             TrayIconBuilder::new()
                                 .with_menu(Box::new(tray_menu))
                                 .with_tooltip(&config.title)
                                 .with_icon(icon)
                                 .build()
                                 .unwrap()
                         );
                    }
                }
                CactusEvent::SetWindowIcon(path) => {
                    if let Some(icon) = load_icon_tao(&path) {
                        window.set_window_icon(Some(icon));
                    }
                }
                CactusEvent::Drag => {
                    let _ = window.drag_window();
                }
                CactusEvent::RegisterShortcut(accel_str, id) => {
                    if let Ok(hotkey) = accel_str.parse::<HotKey>() {
                        let _ = hotkey_manager.register(hotkey);
                        hotkeys.insert(id, hotkey);
                    }
                }
                CactusEvent::CloseSplash => {
                    if let Some(sw) = splash_window.take() {
                        sw.set_visible(false);
                        drop(sw);
                    }
                    _splash_webview.take();
                    window.set_visible(true);
                    window.set_focus();
                }
                CactusEvent::Notification(title, message, icon_path) => {
                    let mut notification = notify_rust::Notification::new();
                    notification.summary(&title).body(&message);
                    if let Some(icon) = icon_path {
                        notification.icon(&icon);
                    }
                    #[cfg(target_os = "windows")]
                    {
                         notification.appname("CactusCat");
                    }
                    let _ = notification.show();
                }
                CactusEvent::SetTaskbarProgress(state, progress) => {
                    #[cfg(target_os = "windows")]
                    {
                        use tao::window::ProgressState;
                        let s = match state.to_lowercase().as_str() {
                            "normal" => ProgressState::Normal,
                            "indeterminate" => ProgressState::Indeterminate,
                            "error" => ProgressState::Error,
                            "paused" => ProgressState::Paused,
                            _ => ProgressState::None,
                        };
                        window.set_progress_bar(tao::window::ProgressBarState {
                            state: Some(s),
                            progress: Some(progress as u64),
                            desktop_filename: None,
                        });
                    }
                }
                CactusEvent::SetAppId(_app_id) => {
                    #[cfg(target_os = "windows")]
                    {
                    }
                }
                CactusEvent::SetFullscreen(fs) => {
                    if fs {
                        window.set_fullscreen(Some(tao::window::Fullscreen::Borderless(None)));
                    } else {
                        window.set_fullscreen(None);
                    }
                }
                CactusEvent::SetResizable(res) => {
                    window.set_resizable(res);
                }
                CactusEvent::SetAlwaysOnTop(on_top) => {
                    window.set_always_on_top(on_top);
                }
                CactusEvent::Hide => {
                    window.set_visible(false);
                }
                CactusEvent::Show => {
                    window.set_visible(true);
                    window.set_focus();
                }
            },
            Event::MainEventsCleared => {
                // muda Menu Events
                if let Ok(event) = MenuEvent::receiver().try_recv() {
                    if let Ok(id_int) = event.id.0.parse::<u32>() {
                        Python::with_gil(|py| {
                            let msg = format!(r#"{{"event": "menu_click", "id": {}}}"#, id_int);
                            if let Err(e) = ipc_cb_for_loop.call1(py, (msg,)) {
                                e.print_and_set_sys_last_vars(py);
                            }
                        });
                    }
                }

                // Global Hotkeys
                if let Ok(event) = GlobalHotKeyEvent::receiver().try_recv() {
                    for (id, hotkey) in &hotkeys {
                        if hotkey.id() == event.id {
                            Python::with_gil(|py| {
                                let msg = format!(r#"{{"event": "shortcut", "id": {}}}"#, id);
                                if let Err(e) = ipc_cb_for_loop.call1(py, (msg,)) {
                                    e.print_and_set_sys_last_vars(py);
                                }
                            });
                        }
                    }
                }
            },
            _ => (),
        }
    });
}
