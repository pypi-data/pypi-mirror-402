from typing import List, Optional, Callable, Union

class MenuItem:
    def __init__(
        self,
        label: str,
        callback: Optional[Callable] = None,
        shortcut: str = "",
        submenu: Optional['Menu'] = None,
        is_separator: bool = False,
    ):
        self.label = label
        self.callback = callback
        self.shortcut = shortcut
        self.submenu = submenu
        self.is_separator = is_separator
        self.id = None  # Assigned by MenuBar

class Menu:
    def __init__(self, title: str = ""):
        self.title = title
        self.items: List[MenuItem] = []

    def add_item(self, label: str, callback: Optional[Callable] = None, shortcut: str = ""):
        item = MenuItem(label, callback, shortcut)
        self.items.append(item)
        return item

    def add_submenu(self, title: str):
        submenu = Menu(title)
        item = MenuItem(title, submenu=submenu)
        self.items.append(item)
        return submenu

    def add_separator(self):
        item = MenuItem("", is_separator=True)
        self.items.append(item)
        return item

class MenuBar:
    def __init__(self):
        self.menus: List[Menu] = []
        self._callbacks = {}
        self._id_counter = 1000

    def add_menu(self, menu_or_title: Union[Menu, str]):
        if isinstance(menu_or_title, str):
             menu = Menu(menu_or_title)
        else:
             menu = menu_or_title
        self.menus.append(menu)
        return menu

    def _prepare(self):
        """
        Walks the menu tree and assigns IDs to items with callbacks.
        Returns a serializable structure for the Rust core.
        """
        self._callbacks = {}
        self._id_counter = 1000
        
        def process_menu(menu):
            serialized_items = []
            for item in menu.items:
                serialized_item = {
                    "label": item.label,
                    "shortcut": item.shortcut,
                    "is_separator": item.is_separator,
                }
                
                if item.submenu:
                    serialized_item["submenu"] = process_menu(item.submenu)
                else:
                    self._id_counter += 1
                    item.id = self._id_counter
                    serialized_item["id"] = item.id
                    if item.callback:
                        self._callbacks[item.id] = item.callback
                
                serialized_items.append(serialized_item)
            return serialized_items

        serialized_menus = []
        for menu in self.menus:
            serialized_menus.append({
                "title": menu.title,
                "items": process_menu(menu)
            })
        return serialized_menus

    def _handle_command(self, cmd_id):
        callback = self._callbacks.get(cmd_id)
        if callback:
            callback()
            return True
        return False
