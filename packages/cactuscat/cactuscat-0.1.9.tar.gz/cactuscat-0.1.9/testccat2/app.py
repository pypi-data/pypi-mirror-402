from cactuscat import App

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
