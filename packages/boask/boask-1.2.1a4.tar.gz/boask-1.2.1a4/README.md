<h1 align="center">Boask</h1>
<div align="center"><img src="https://0xopx.github.io/some-things-lol/boask/logo.svg" alt="Boask Logo" /><br>
Minimal website engine. <br>
</div>

**Source (GitHub): [GitHub Link](https://github.com/OXOPSoftware/boask.git) *(If you are on GitHub, please do not expect stable versions when there is a alpha version, it will get the alpha version, and will get version first)***
```bash
pip install boask
```
# Quick Start
```python
from boask import route, use, run_server, html_templates

@route("/")
def home(handler):
    return html_templates.render("home.html", title="Boask")

if __name__ == "__main__":
    run_server(debug=True, host="127.0.0.1", port=5000)
```

Make sure you are creating, at your project directory level, a `templates` folder containing the `home.html` file. When it starts, go to localhost:5000.
# Comparison to Flask
1. Lightweight.
2. Unlike Flask, it's for beginners, and movers from Flask.
3. No `{{ url_for('static', filename='css/main.css') }}` (example), we use `/static/css/main.css` for example!
# Info
1. Do not install a earlier version than 1.0.4, you can 1.0.0 but that one is not supported! You can't import them! Also, do not install 1.1.4! It had a bug in strict slashes and it did 500 always! I don't know how the 1.1.4 issue happened! Do not install 1.1.5a2 also! It has import error instead of import .error
# Changelog
## Now uses `pyproject.toml` instead of `setup.py`!