from demo_app import app
from poridhiweb.models.responses import Response, HTMLResponse


@app.route('/static')
def static_view(request) -> Response:
    return HTMLResponse(content="<h1>This is a static view</h1>")


@app.route('/dashboard')
def dashboard(request) -> Response:
    name = "Dipanjal"
    title = "Dashboard View"
    html_content = app.template("dashboard.html", context={"name": name, "title": title})
    return HTMLResponse(content=html_content)
