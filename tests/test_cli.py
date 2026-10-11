from doc_extract.cli import main


def args(server, *more):
    return ["--base-url", server.base_url, "--model", "m", *more]


def test_single_to_stdout(server, make_image, capsys):
    assert main([str(make_image()), "--stdout", *args(server)]) == 0
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


def test_default_writes_next_to_input(server, make_image):
    img = make_image("scan.png")
    assert main([str(img), *args(server)]) == 0
    assert img.with_name("scan.md").read_text().startswith("text-")


def test_default_many_next_to_inputs(server, make_image):
    a, b = make_image("a.png"), make_image("b.png")
    assert main([str(a), str(b), *args(server)]) == 0
    assert a.with_name("a.md").exists() and b.with_name("b.md").exists()


def test_many_to_folder_uses_stem(server, make_image, tmp_path):
    a, b = make_image("a.png"), make_image("b.png")
    out = tmp_path / "out"
    assert main([str(a), str(b), "-o", str(out), *args(server)]) == 0
    assert sorted(p.name for p in out.iterdir()) == ["a.md", "b.md"]


def test_stdout_and_output_conflict(server, make_image, tmp_path, capsys):
    code = main([str(make_image()), "--stdout", "-o", str(tmp_path / "x.md"), *args(server)])
    assert code == 2


def test_many_stdout_headers(server, make_image, capsys):
    a, b = make_image("a.png"), make_image("b.png")
    assert main([str(a), str(b), "--stdout", *args(server)]) == 0
    out = capsys.readouterr().out
    assert out.index("<!-- file: a.png -->") < out.index("<!-- file: b.png -->")


def test_failure_exit_code_and_rest_written(server, make_image, tmp_path, capsys):
    good = make_image("g.png")
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"x")
    out = tmp_path / "out"
    code = main([str(bad), str(good), "-o", str(out), *args(server)])
    assert code == 1
    assert (out / "g.md").exists() and not (out / "bad.md").exists()
    assert "bad.png" in capsys.readouterr().err


def test_missing_config_exit_2(make_image, capsys):
    assert main([str(make_image())]) == 2
    assert "base_url" in capsys.readouterr().err


def test_limit_flag(server, make_pdf, capsys):
    code = main([str(make_pdf(pages=3)), "--max-pages", "2", *args(server)])
    assert code == 1
    assert "max_pages" in capsys.readouterr().err
