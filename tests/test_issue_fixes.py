import os
import shutil

import pandas as pd
import pytest

from nisupply import io, structure


def test_discovery(tmp_path):
    for subdir in ("pre/standard", "pre/standard_direct", "post/standard_direct"):
        directory = tmp_path / subdir
        directory.mkdir(parents=True)
        for name in ("cat_12.xml", "other.xml"):
            (directory / name).touch()
    df = io.get_filepath_df(
        tmp_path, filename_regex=r"^cat_.*\.xml$", regex_match=r"/pre/",
        exclude_nested_dirs="pre/standard", regex_dict={"id": r"cat_(\d)(\d)"},
    )
    assert df.to_dict("records") == [
        {"filepath": str(tmp_path / "pre/standard_direct/cat_12.xml"), "id": "1"}
    ]


def test_cache_snapshot(tmp_path):
    root = tmp_path / "src"
    root.mkdir()
    (root / "a.txt").touch()
    first = io.get_filepath_df(root, cache=tmp_path / "cache")
    (root / "b.txt").touch()
    assert io.get_filepath_df(root, cache=tmp_path / "cache").equals(first)
    assert len(io.get_filepath_df(root)) == 2
    assert len(io.get_filepath_df(root, cache=tmp_path / "cache", file_prefix="b")) == 1


def test_columns():
    df = pd.DataFrame({"src": ["a/image.nii", "c/motion.txt"], "id": [1, 2]}, index=[4, 6])
    structure.build_column(df, "sub-{id:02d}", "subject")
    structure.join_path(df, "out", "{subject}", new_col="folder")
    structure.set_dir(df, "dest", src_col="src")
    assert df.folder.tolist() == [os.path.join("out", s) for s in ("sub-01", "sub-02")]
    assert df.dst.tolist() == [os.path.join("dest", n) for n in ("image.nii", "motion.txt")]
    structure.add_match_column(df, "src", "kind", {".nii": "image", ".txt": "motion"})
    assert df.kind.tolist() == ["image", "motion"]
    structure.add_match_column(df, "src", "kind", {r"\.nii$": "scan"}, regex=True, default="other")
    assert df.kind.tolist() == ["scan", "other"]


def test_copy_resume(tmp_path, monkeypatch):
    src = tmp_path / "input"
    tgt = tmp_path / "output"
    src.write_bytes(b"new")
    tgt.write_bytes(b"old")
    df = pd.DataFrame({"src": [src], "dst": [tgt]})
    io.copy_files(df, "src", "dst", skip_existing=True)
    assert tgt.read_bytes() == b"old"
    io.copy_files(df, "src", "dst", skip_existing=True, verify=True)
    assert tgt.read_bytes() == b"new"

    def interrupted(source, temporary):
        temporary.write_bytes(b"x")
        raise OSError("interrupted")

    monkeypatch.setattr(shutil, "copy2", interrupted)
    io.copy_files(df, "src", "dst", skip_existing=True, verify=True)
    with pytest.raises(OSError, match="interrupted"):
        io.copy_files(df, "src", "dst")
    assert tgt.read_bytes() == b"new"
    assert set(tmp_path.iterdir()) == {src, tgt}


@pytest.mark.skipif(shutil.which("rsync") is None, reason="requires rsync")
def test_sync(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "src"
    folder = root / "sub-1"
    folder.mkdir(parents=True)
    source = folder / "space and\nnewline"
    source.write_bytes(b"scan")
    (folder / "other").touch()
    df = pd.DataFrame({"src": [source.relative_to(root)]})
    target = tmp_path / "nested" / "dst"
    io.rsync_from_df(df, "src", root, target)
    assert (target / "sub-1" / source.name).read_bytes() == b"scan"
    assert not (target / "sub-1/other").exists()
    assert not list(tmp_path.glob(".rsync-*"))
    with pytest.raises(ValueError):
        io.rsync_from_df(pd.DataFrame({"src": ["../outside"]}), "src", root, target)


def test_bids(tmp_path):
    pytest.importorskip("bids")
    from nisupply.bids import bids_regex_dict

    file = tmp_path / "sub-01" / "sub-01_task-rest_bold.nii.gz"
    file.parent.mkdir()
    file.touch()
    df = io.get_filepath_df(tmp_path, regex_dict=bids_regex_dict("subject", "task"))
    assert df.loc[0, ["subject", "task"]].tolist() == ["01", "rest"]


def test_nipype(tmp_path):
    pytest.importorskip("nipype")
    from nisupply.workflows import discovery_workflow

    file = tmp_path / "image.nii"
    file.touch()
    workflow = discovery_workflow(tmp_path, file_suffix=".nii")
    workflow.base_dir = str(tmp_path / "work")
    graph = workflow.run()
    assert next(iter(graph.nodes())).result.outputs.files == [str(file)]
