from housing_explorer.cli import main


def test_clean_command_writes_output(sample_path, tmp_path, capsys):
    out = tmp_path / "clean.csv"
    assert main(["clean", str(sample_path), "-o", str(out)]) == 0
    assert out.exists()
    assert "rows kept: 9" in capsys.readouterr().out


def test_missing_file_returns_error(tmp_path, capsys):
    assert main(["clean", str(tmp_path / "nope.csv")]) == 1
    assert "error:" in capsys.readouterr().err
