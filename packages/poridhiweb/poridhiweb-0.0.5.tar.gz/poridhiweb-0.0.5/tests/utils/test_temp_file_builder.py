from tests.utils.temp_file_builder import TempFileBuilder


def test_temp_file_builder(tmpdir_factory):
    builder = TempFileBuilder(tmpdir_factory)

    # Build the file structure
    builder.create_child_dir("css") \
        .create_file("style.css") \
        .set_file_content("body { margin: 0; }") \
        .go_to_parent() \
        .create_child_dir("js") \
        .create_file("script.js") \
        .set_file_content("console.log('hello');") \
        .go_to_root() \
        .create_file("index.html") \
        .set_file_content("<html></html>")

    builder.print_tree()
    # Output:
    # └── static/
    #     ├── css/
    #     │   └── style.css (20 bytes)
    #     ├── js/
    #     │   └── script.js (21 bytes)
    #     └── index.html (13 bytes)

    # Access file content through nodes
    css_file = builder.find_node("style.css")
    print(css_file.get_content())  # "body { margin: 0; }"

    # Navigate and access files
    builder.go_to_child("css")
    style_node = builder.get_file_node("style.css")
    print(style_node.content)  # "body { margin: 0; }"
