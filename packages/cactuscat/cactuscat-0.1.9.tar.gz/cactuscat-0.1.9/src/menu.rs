use serde::Deserialize;
use muda::{MenuItem, Submenu, PredefinedMenuItem, MenuId};

#[derive(Deserialize)]
pub struct MenuSchema {
    pub title: String,
    pub items: Vec<MenuItemSchema>,
}

#[derive(Deserialize)]
pub struct MenuItemSchema {
    pub label: String,
    #[serde(default)]
    pub id: u16,
    #[serde(default)]
    pub is_separator: bool,
    #[serde(default)]
    pub submenu: Option<Vec<MenuItemSchema>>,
}

pub fn build_menu_recursive(items: Vec<MenuItemSchema>) -> Vec<Box<dyn muda::IsMenuItem>> {
    let mut result: Vec<Box<dyn muda::IsMenuItem>> = Vec::new();
    for item in items {
        if item.is_separator {
            result.push(Box::new(PredefinedMenuItem::separator()));
        } else if let Some(sub_items) = item.submenu {
            let submenu = Submenu::new(&item.label, true);
            let children = build_menu_recursive(sub_items);
            for child in children {
                submenu.append(child.as_ref()).unwrap();
            }
            result.push(Box::new(submenu));
        } else {
            let menu_item = MenuItem::with_id(MenuId::new(item.id.to_string()), &item.label, true, None);
            result.push(Box::new(menu_item));
        }
    }
    result
}
