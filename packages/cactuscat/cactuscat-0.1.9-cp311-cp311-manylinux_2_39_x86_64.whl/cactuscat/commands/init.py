from pathlib import Path
import os
import sys
import json
import shutil
import subprocess
from ..apputils.console import (
    log,
    console,
    get_progress,
    print_rule,
    run_command_with_output,
)

# --- Templates ---

TEMPLATE_APP = """from cactuscat import App

def main():
    # 'title' and 'url' will be loaded from settings.json if not provided
    app = App()
    
    # Expose Python function to Frontend
    @app.expose
    def greet(name):
        return f"Hello, {name}! From Python 🌵"

    app.run()

if __name__ == '__main__':
    main()
"""

# --- Helpers ---

def get_frontend_runner(provider: str) -> str:
    if provider == "bun":
        return "bunx"
    if provider == "pnpm":
        return "pnpx"
    return "npx"


def init_project(args):
    # Determine project name and target directory
    if args.name == ".":
        project_name = os.path.basename(os.getcwd())
        target = Path(os.getcwd())
    else:
        project_name = args.name
        target = Path(os.getcwd()) / project_name

    if args.name != "." and target.exists():
        log(f"Error: Target '{target}' already exists.", style="error")
        return 1
    
    if args.name != "." and not target.exists():
        target.mkdir(parents=True)

    print_rule(f"Initializing CactusCat App: {project_name}")

    # 1. Create app.py
    app_file = target / "app.py"
    if not app_file.exists():
        app_file.write_text(TEMPLATE_APP, encoding="utf-8")

    # 2. Create requirements.json
    req_file = target / "requirements.json"
    if not req_file.exists():
        req_data = {
            "dependencies": ["rich", "watchfiles"],
            "plugins": []
        }
        req_file.write_text(json.dumps(req_data, indent=4))

    # 3. Create settings.json
    is_next = args.template.lower() in ["next", "nextjs"]
    dist_path = "frontend/out/index.html" if is_next else "frontend/dist/index.html"
    
    settings_data = {
        "title": project_name,
        "version": "0.1.0",
        "author": "Your Name",
        "description": "A CactusCat Application",
        "copyright": f"Copyright © 2026 Your Name",
        "cactuscat_version": "0.1.0",
        "dimensions": [800, 600],
        "min_size": None,
        "max_size": None,
        "resizable": True,
        "frameless": False,
        "fullscreen": False,
        "always_on_top": False,
        "transparent": False,
        "background_color": "#ffffff",
        "start_maximized": False,
        "start_hidden": False,
        "url": f"ccat://localhost/{dist_path}",
        "icon": "icon.ico",
        "engine": "native",
        "single_instance": True,
        "debug": True,
        "frontend_framework": args.template,
        "frontend_provider": "npm",
        "dev_port": 5173,
        "plugins": []
    }
    
    settings_file = target / "settings.json"
    if not settings_file.exists():
        settings_file.write_text(json.dumps(settings_data, indent=4))

    # 3. Create requirements.json
    req_data = {"dependencies": ["cactuscat"]}
    (target / "requirements.json").write_text(json.dumps(req_data, indent=4))

    # 4. Scaffold Frontend
    frontend_dir = target / "frontend"
    if not frontend_dir.exists():
        log(f"Scaffolding {args.template} frontend...", style="info")
        try:
            runner = "npx"
            is_win = sys.platform == "win32"
            
            if is_next:
                 cmd = [runner, "-y", "create-next-app@latest", "frontend", "--use-npm", "--no-git", "--ts", "--eslint", "--src-dir", "--app"]
                 run_command_with_output(cmd, cwd=str(target), shell=is_win)
                 
                 next_config_path = frontend_dir / "next.config.mjs"
                 if not next_config_path.exists(): next_config_path = frontend_dir / "next.config.js"
                 next_config_path.write_text("""/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
};
export default nextConfig;""", encoding="utf-8")

            else:
                # Vite (default)
                # Pin create-vite to 5.4.10 to avoid experimental prompts (rolldown etc)
                cmd = [runner, "-y", "create-vite@5.4.10", "frontend", "--template", args.template]
                run_command_with_output(cmd, cwd=str(target), shell=is_win)
            
            # 4.5 Copy Client Library
            log("Bundling CactusCat Client...", style="dim")
            pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            client_lib_src = os.path.join(pkg_root, "ccat")
            client_lib_dest = frontend_dir / "ccat"
            
            if os.path.exists(client_lib_src):
                if os.path.exists(client_lib_dest): shutil.rmtree(client_lib_dest)
                shutil.copytree(client_lib_src, client_lib_dest)
                
                client_pkg_json = client_lib_dest / "package.json"
                if not client_pkg_json.exists():
                    client_pkg_json.write_text(json.dumps({
                        "name": "ccat",
                        "version": "0.1.9",
                        "main": "index.js",
                        "type": "module"
                    }, indent=2))
            else:
                log(f"Warning: Client library not found at {client_lib_src}", style="warning")

            # 5. Configure package.json
            log("Configuring frontend dependencies...", style="dim")
            pkg_path = frontend_dir / "package.json"
            if pkg_path.exists():
                pkg_data = json.loads(pkg_path.read_text())
                
                if "dependencies" not in pkg_data: pkg_data["dependencies"] = {}
                pkg_data["dependencies"]["ccat"] = "file:./ccat"
                
                if "devDependencies" not in pkg_data: pkg_data["devDependencies"] = {}
                pkg_data["devDependencies"]["@vitejs/plugin-legacy"] = "^5.0.0"
                pkg_data["devDependencies"]["vite"] = "^5.0.0"
                
                pkg_path.write_text(json.dumps(pkg_data, indent=2))

            # --- INJECT STARTER CODE ---
            if "react" in args.template:
                app_jsx = frontend_dir / "src" / "App.jsx"
                if not app_jsx.exists(): app_jsx = frontend_dir / "src" / "App.tsx"

                if app_jsx.exists():
                    app_jsx.write_text("""import { useState, useEffect } from 'react'
import ccat from 'ccat'
import './App.css'

function App() {
  const [msg, setMsg] = useState("Click to greet Python 🌵")
  const [count, setCount] = useState(0)

  // Listen for state sync
  useEffect(() => {
    const handleState = (e) => {
        if (e.detail.key === 'count') setCount(e.detail.value);
    }
    window.addEventListener('cactus:state', handleState);
    return () => window.removeEventListener('cactus:state', handleState);
  }, [])

  const handleGreet = async () => {
    try {
      const response = await ccat.greet("React Developer")
      setMsg(response)
      
      // Update shared state
      ccat.state.count = (ccat.state.count || 0) + 1
    } catch (err) {
      console.error(err)
      setMsg("Error: " + err)
    }
  }

  return (
    <div className="card">
        <h1>CactusCat + React 🌵</h1>
        <p>{msg}</p>
        <button onClick={handleGreet}>
          Greet Python (Count: {count})
        </button>
        <p>
          Edit <code>src/App.jsx</code> and save to test HMR
        </p>
    </div>
  )
}

export default App
""", encoding="utf-8")
                    log("Injected React starter code with CactusCat Client", style="success")
            
            # Install
            log("Installing frontend packages...", style="dim")
            run_command_with_output(["npm", "install"], cwd=str(frontend_dir), shell=is_win)
            
            # Configure Vite Config
            if not is_next:
                vite_config_path = frontend_dir / "vite.config.js"
                if not vite_config_path.exists(): vite_config_path = frontend_dir / "vite.config.ts"
                
                # Detect template type for correct config
                is_react = "react" in args.template
                is_vue = "vue" in args.template
                
                config_content = ""
                if is_react:
                    config_content = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import legacy from '@vitejs/plugin-legacy'

// https://vitejs.dev/config/
export default defineConfig({
  base: './', 
  plugins: [
    react(),
    legacy({
      targets: ['defaults', 'not IE 11'],
    }),
  ],
})"""
                elif is_vue:
                    config_content = """import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import legacy from '@vitejs/plugin-legacy'

// https://vitejs.dev/config/
export default defineConfig({
  base: './',
  plugins: [
    vue(),
    legacy({
      targets: ['defaults', 'not IE 11'],
    }),
  ],
})"""
                else:
                    # Vanilla or others
                    config_content = """import { defineConfig } from 'vite'
import legacy from '@vitejs/plugin-legacy'

export default defineConfig({
  base: './', // Crucial for ccat:// loading relative assets
  plugins: [
    legacy({
      targets: ['defaults', 'not IE 11'],
    }),
  ],
})"""

                vite_config_path.write_text(config_content, encoding="utf-8")
                
        except Exception as e:
            log(f"Frontend setup failed: {e}", style="error")
            import traceback
            traceback.print_exc()

    # 6. Create Virtual Environment
    env_dir = target / "env"
    if not env_dir.exists():
        log("Creating virtual environment...", style="info")
        subprocess.run([sys.executable, "-m", "venv", str(env_dir)], check=True)
        
        log("Installing Python dependencies...", style="dim")
        if sys.platform == "win32":
            pip = env_dir / "Scripts" / "pip"
        else:
            pip = env_dir / "bin" / "pip"
            
        subprocess.run([str(pip), "install", "cactuscat"], check=True)

    # 7. Create Run Scripts
    if sys.platform == "win32":
        (target / "run.bat").write_text("@echo off\ncall env\\Scripts\\activate.bat\npython app.py\npause", encoding="utf-8")
    else:
        run_sh = target / "run.sh"
        run_sh.write_text("#!/bin/bash\nsource env/bin/activate\npython app.py", encoding="utf-8")
        try:
            run_sh.chmod(run_sh.stat().st_mode | 0o111)
        except: pass

    log(f"Project '{project_name}' initialized successfully!", style="success")
    console.print(f"👉 cd {project_name}")
    console.print("cactuscat run")
    return 0
