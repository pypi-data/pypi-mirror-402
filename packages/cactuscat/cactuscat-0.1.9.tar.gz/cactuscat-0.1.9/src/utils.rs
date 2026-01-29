use tao::window::Icon as TaoIcon;
use tray_icon::Icon as TrayIconType;

pub fn load_icon_tao(path: &str) -> Option<TaoIcon> {
    let image = image::open(path).ok()?;
    let (width, height) = (image.width(), image.height());
    let rgba = image.into_rgba8().into_raw();
    TaoIcon::from_rgba(rgba, width, height).ok()
}

pub fn load_icon_tray(path: &str) -> Option<TrayIconType> {
    let image = image::open(path).ok()?;
    let (width, height) = (image.width(), image.height());
    let rgba = image.into_rgba8().into_raw();
    TrayIconType::from_rgba(rgba, width, height).ok()
}
