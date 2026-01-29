/// Custom events to control the application from Python threads
#[derive(Debug)]
pub enum CactusEvent {
    Eval(String),
    Minimize,
    Maximize,
    Restore,
    Close,
    SetTitle(String),
    SetMenu(String),
    RegisterShortcut(String, u32),
    SetTray(String, Option<String>), // JSON menus, optional icon path
    SetWindowIcon(String),
    Drag,
    CloseSplash,
    Notification(String, String, Option<String>), // Title, Message, IconPath
    SetTaskbarProgress(String, u32), // State, Progress
    SetAppId(String),
    SetFullscreen(bool),
    SetResizable(bool),
    SetAlwaysOnTop(bool),
    Hide,
    Show,
}
