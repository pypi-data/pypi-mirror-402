from poridhiweb import PoridhiFrame
from tests.constants import BASE_URL
from requests import Session as RequestsSession
from wsgiadapter import WSGIAdapter as RequestsWSGIAdapter


class TestFramework(PoridhiFrame):
    def test_session(self, base_url=BASE_URL):
        session = RequestsSession()
        session.mount(
            prefix=base_url,
            adapter=RequestsWSGIAdapter(app=self)
        )
        return session


class TestFrameworkBuilder:
    def __init__(self):
        self.kwargs = {}

    def template_dir(self, template_dir: str):
        self.kwargs["template_dir"] = template_dir
        return self

    def static_dir(self, static_dir: str):
        self.kwargs["static_dir"] = static_dir
        return self

    def build(self):
        return TestFramework(**self.kwargs)

