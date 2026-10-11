from doc_extract.cli import main


def args(server, *more):
    return ["--base-url", server.base_url, "--model", "m", *more]


def test_single_to_stdout(server, make_image, capsys):
    assert main([str(make_image()), *args(server)]) == 0
    assert capsys.readouterr().out.startswith("text-")


def test_single_to_file(server, make_image, tmp_path):
    out = tmp_path / "out.md"
    assert main([str(make_image()), "-o", str(out), *args(server)]) == 0
    assert out.read_text().startswith("text-")


def test_many_to_folder_no_collision(server, make_image, tmp_path):
    a_png, a_jpg = make_image("a.png"), make_image("a.jpg")
    out = tmp_path / "out"
    assert main([str(a_png), str(a_jpg), "-o", str(out), *args(server)]) == 0
    assert sorted(p.name for p in out.iterdir()) == ["a.jpg.md", "a.png.md"]


def test_many_stdout_headers(server, make_image, capsys):
    a, b = make_image("a.png"), make_image("b.png")
    assert main([str(a), str(b), *args(server)]) == 0
    out = capsys.readouterr().out
    assert out.index("<!-- file: a.png -->") < out.index("<!-- file: b.png -->")


def test_failure_exit_code_and_rest_written(server, make_image, tmp_path, capsys):
    good = make_image("g.png")
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"x")
    out = tmp_path / "out"
    code = main([str(bad), str(good), "-o", str(out), *args(server)])
    assert code == 1
    assert (out / "g.png.md").exists() and not (out / "bad.png.md").exists()
    assert "bad.png" in capsys.readouterr().err


def test_missing_config_exit_2(make_image, capsys):
    assert main([str(make_image())]) == 2
    assert "base_url" in capsys.readouterr().err


def test_limit_flag(server, make_pdf, capsys):
    code = main([str(make_pdf(pages=3)), "--max-pages", "2", *args(server)])
    assert code == 1
    assert "max_pages" in capsys.readouterr().err
