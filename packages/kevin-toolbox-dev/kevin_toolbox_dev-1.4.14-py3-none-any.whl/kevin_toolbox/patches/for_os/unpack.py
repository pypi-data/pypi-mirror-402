import os

BACKEND = ["tarfile", "os"]


def unpack(source, target=None):
    assert os.path.exists(source)
    target = os.path.dirname(source) if target is None else target
    os.makedirs(target, exist_ok=True)

    try:
        assert "tarfile" in BACKEND
        import tarfile
        # 创建一个 TarFile 对象并打开 tar 文件
        with tarfile.open(source, "r") as tar:
            # 遍历 tar 文件中的每个文件或目录
            for member in tar.getmembers():
                # 如果成员是一个文件，则提取到目标目录中
                if member.isfile():
                    tar.extract(member, target)
                # 如果成员是一个目录，则在目标目录中创建相应的目录结构
                elif member.isdir():
                    os.makedirs(os.path.join(target, member.name), exist_ok=True)
    except:
        assert "os" in BACKEND
        os.system(f'cd {target}; tar -xvf {source}')

    assert os.path.exists(target), \
        f'failed to unpack tar file {source}'
