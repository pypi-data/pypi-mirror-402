# CactusCat

> **The ultra-fast, Rust-powered bridge between Python and the Web.**

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Rust](https://img.shields.io/badge/rust-%23000000.svg?style=for-the-badge&logo=rust&logoColor=white)
![Wry](https://img.shields.io/badge/Powered%20By-Wry-orange?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-green)

CactusCat is a modern, high-performance hybrid framework designed to build desktop applications using **Python** for logic and **Modern Web Tech** (React, Vue, Svelte, Next.js) for the UI. Rebuilt from the ground up in Rust, it provides a "Zero-Cost" abstraction layer for enterprise-grade applications.

---

## Recent Evolution: The "Betrayal of Tauri"

CactusCat has evolved beyond a simple WebView wrapper. It is now a **Multi-Engine Application Platform**.

- **CNB (Cactus Native Bundle):** A new hybrid packaging paradigm. We use PyInstaller for dependency analysis (tree-shaking) but replace the actual bundling with a **high-performance Rust Packer**. 
- **Shielded VFS Bootloader:** Applications run inside a memory-backed, isolated, and encrypted Virtual File System. Your source code never touches the disk in plain text.
- **Multi-Engine Hotswapping:** Hotswap your browser backend with a single CLI flag. Use the lightweight **Native Engine** (Tao/Wry) for performance, or the **Chrome Engine** (Enterprise Chromium stack) for full web compatibility.
- **Aggressive Pruning:** The native Rust packer prunes non-essential metadata (`.dist-info`, test suites, docs) resulting in binaries significantly smaller than standard Python bundlers.

---

## Features

- **Native Rust Engine:** Built on `tao` and `wry`, eliminating legacy `ctypes` overhead.
- **Multi-Engine Runtime:** Choose between Native WebView or a full Chromium/Electron stack.
- **Reactive State:** Magic bi-directional sync between Python `app.state` and JavaScript `ccat.state`.
- **Zstd-Compressed Archives:** Custom `.cat` archive format for ultra-fast startup and small footprints.
- **MetaEdit Integration:** Powered by the brand new `metaedit` Rust crate for 1:1 binary metadata surgery.
- **Powerhouse CLI:** One-stop shop for initializing, running, and packaging your apps.

---

##  Quick Start

### 1. Installation
Install the development version (pre-compiled wheels available):
```bash
pip install cactuscat
```

### 2. Scaffold a New Project
```bash
cactuscat init MySweetApp --template react
```

### 3. Run with Engine Hotswapping
```bash
# Default Native Run
cactuscat run --dev

# Run with Enterprise Chrome Engine
cactuscat run --dev --engine chrome
```

---

## Code Example

### Python Backend (`app.py`)
```python
from cactuscat import App

app = App()
app.state.counter = 0

@app.expose
def increment():
    app.state.counter += 1
    return f"Count is now {app.state.counter}"

app.run()
```

### Frontend UI (`App.jsx`)
```javascript
import ccat from 'ccat' // Unified CactusCat Client

async function handleAction() {
    // Dynamic Python calling
    const msg = await ccat.increment();
    console.log(msg);
    
    // Access reactive state directly
    console.log(ccat.state.counter); 
}
```

---

##  CLI Reference

| Command | Description |
| :--- | :--- |
| `init` | Scaffold a project with React, Vue, Svelte, or Next.js. |
| `run --dev` | Launch backend + frontend dev server with hot-reload. |
| `run --engine <name>` | Launch with a specific engine (`native` or `chrome`). |
| `package --native` | Trigger the [CNB] workflow with aggressive Rust pruning. |
| `package --secure` | Build a native Rust bootloader with an encrypted payload. |
| `engine install` | Manage browser runtimes (e.g., download Chrome engine). |
| `doctor` | Comprehensive system health and dependency check. |

---

## Architecture: The CNB Paradigm

Unlike traditional "OneDir" or "OneFile" approaches, CactusCat's **Native Bundle** logic works in three stages:
1. **Analysis:** PyInstaller maps the dependency tree.
2. **Pruning:** Rust strips the "fat" (PDFs, tests, info folders) and Compresses.
3. **Execution:** A Rust Bootloader initializes a shielded environment, decrypts the `ccat://` assets, and executes the entry point from memory.

---

## License
CactusCat is open-source software licensed under the MIT License.
