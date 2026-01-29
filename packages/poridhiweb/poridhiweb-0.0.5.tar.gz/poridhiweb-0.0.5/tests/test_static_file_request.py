from tests.constants import BASE_URL
from tests.utils.temp_file_builder import TempFileBuilder
from tests.utils.test_framework import TestFrameworkBuilder

FILE_DIR = "css"
FILE_NAME = "main.css"
FILE_CONTENTS = "body {background-color: red}"

def test_requested_static_file_does_not_exist(temp_file_builder: TempFileBuilder):
    static_root = temp_file_builder.root

    app = TestFrameworkBuilder().static_dir(static_root).build()
    client = app.test_session()
    response = client.get(f"{BASE_URL}/{FILE_DIR}/{FILE_NAME}")

    assert response.status_code == 404


def test_requested_static_file_exists(temp_file_builder: TempFileBuilder):
    static_root = str(temp_file_builder.root)
    (
        temp_file_builder
        .create_file(FILE_NAME)
        .set_file_content(FILE_CONTENTS)
    )

    app = TestFrameworkBuilder().static_dir(static_root).build()
    client = app.test_session()
    response = client.get(f"{BASE_URL}/{FILE_NAME}")

    assert response.status_code == 200
    assert response.text == FILE_CONTENTS


def test_requested_static_file_exists_in_sub_dir(temp_file_builder: TempFileBuilder):
    static_root = str(temp_file_builder.root)
    (
        temp_file_builder
        .create_child_dir(FILE_DIR)
        .create_file(FILE_NAME)
        .set_file_content(FILE_CONTENTS)
    )

    app = TestFrameworkBuilder().static_dir(static_root).build()
    client = app.test_session()
    response = client.get(f"{BASE_URL}/{FILE_DIR}/{FILE_NAME}")

    assert response.status_code == 200
    assert response.text == FILE_CONTENTS
