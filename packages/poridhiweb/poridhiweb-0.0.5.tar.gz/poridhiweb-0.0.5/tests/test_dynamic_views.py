from poridhiweb.models.responses import HTMLResponse
from tests.constants import BASE_URL


def test_dynamic_dashboard(app, client):

    @app.route("/dashboard")
    def test_handler(req):
        html_content = app.template(template_name="dashboard.html", context={"name": "test_user", "title": "test_title"})
        return HTMLResponse(html_content)

    response = client.get(f"{BASE_URL}/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["Content-Type"]
    assert "test_user" in response.text
    assert "test_title" in response.text
