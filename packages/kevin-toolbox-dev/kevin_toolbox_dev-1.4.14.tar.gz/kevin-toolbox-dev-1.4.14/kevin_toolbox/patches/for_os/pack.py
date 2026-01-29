import os

BACKEND = ["tarfile", "os"]


def pack(source, target=None):
    assert os.path.exists(source)
    target = source + ".tar" if target is None else target
    os.makedirs(os.path.dirname(target), exist_ok=True)

    try:
        assert "tarfile" in BACKEND
        import tarfile
        with tarfile.open(target, mode="w:gz") as archive:
            archive.add(source, arcname=os.path.basename(source))
    except:
        assert "os" in BACKEND
        p_0, p_1 = os.path.dirname(source), os.path.basename(source)
        os.system(f'cd {p_0}; tar -cvf {target} {p_1}')

    assert os.path.isfile(target), \
        f'failed to pack into tar'
