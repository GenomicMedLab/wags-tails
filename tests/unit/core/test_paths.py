from wags_tails.core.paths import DATA_DIR_ENVVAR, resolve_data_dir


def test_resolve_data_dir_explicit_root_takes_precedence(tmp_path, monkeypatch):
    monkeypatch.setenv(DATA_DIR_ENVVAR, "/some/other/path")

    result = resolve_data_dir(tmp_path)

    assert result == tmp_path.resolve()


def test_resolve_data_dir_from_environment(monkeypatch, tmp_path):
    monkeypatch.setenv(DATA_DIR_ENVVAR, str(tmp_path))

    result = resolve_data_dir()

    assert result == tmp_path.resolve()


def test_resolve_data_dir_uses_default_when_no_root_or_env(monkeypatch, tmp_path):
    monkeypatch.delenv(DATA_DIR_ENVVAR, raising=False)

    monkeypatch.setattr(
        "wags_tails.core.paths.default_data_dir",
        lambda: tmp_path,
    )

    result = resolve_data_dir()

    assert result == tmp_path


def test_resolve_data_dir_expands_user(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    result = resolve_data_dir("~/wags-tails")

    assert result == (tmp_path / "wags-tails").resolve()


def test_resolve_data_dir_does_not_create_directory(tmp_path):
    path = tmp_path / "does-not-exist"

    result = resolve_data_dir(path)

    assert result == path.resolve()
    assert not path.exists()
