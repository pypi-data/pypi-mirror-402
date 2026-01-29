import pytest
from kevin_toolbox.patches.for_test import check_consistency
import os
import numpy as np
from kevin_toolbox.data_flow.file import kevin_notation
from kevin_toolbox.data_flow.file.kevin_notation.test.test_data.data_all import metadata_ls, content_ls, file_path_ls


@pytest.mark.parametrize("expected_metadata, expected_content, file_path",
                         zip(metadata_ls[:], content_ls[:], file_path_ls[:]))
def test_reader(expected_metadata, expected_content, file_path):
    print("test Reader")

    # 读取
    chunk_size = np.random.randint(1, 10)
    with kevin_notation.Reader(file_path=file_path, chunk_size=chunk_size) as reader:
        # metadata
        # print(reader.metadata)
        check_consistency(expected_metadata, reader.metadata)
        # content
        content = next(reader)
        for chunk in reader:
            for key in content.keys():
                content[key].extend(chunk[key])
        check_consistency(expected_content, content)


@pytest.mark.parametrize("expected_metadata, expected_content, file_path",
                         zip(metadata_ls, content_ls, file_path_ls))
def test_writer_0(expected_metadata, expected_content, file_path):
    """
        测试以 writer.key = value 的方式写入
            注意需要以在写入前后按照顺序依次调用 writer.metadata_begin()/end() 和 writer.contents_begin()/end()
    """
    print("test Writer")

    # 新建
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test_data/temp",
                             os.path.basename(file_path))
    part = np.random.randint(1, 5)
    values = list(zip(*[expected_content[key][:-part] for key in expected_metadata["column_name"]]))
    with kevin_notation.Writer(file_path=file_path, mode="w", sep=expected_metadata["sep"]) as writer:
        writer.metadata_begin()
        if part % 2 == 0:
            # 逐个写入
            for key, value in expected_metadata.items():
                if key == "sep":
                    pass
                elif key == "column_name":
                    writer.column_name = value
                elif key == "column_type":
                    # 尝试使用局部指定的 sep
                    writer.column_type = {"value": value, "sep": " "}
                else:
                    writer.write_metadata(key=key, value=value)
        else:
            # 整体写入
            writer.metadata = expected_metadata
        writer.metadata_end()

        writer.contents_begin()
        writer.row_ls = values  # 列表方式写入
        writer.contents_end()

    # 续写
    # values = list(zip(*[expected_content[key][-part:] for key in expected_metadata["column_name"]]))
    values = {k: v[-part:] for k, v in expected_content.items()}
    with kevin_notation.Writer(file_path=file_path, mode="a") as writer:
        writer.column_dict = values  # 字典方式写入
        writer.contents_end()

    # 检验
    with kevin_notation.Reader(file_path=file_path, chunk_size=1000) as reader:
        # metadata
        check_consistency(expected_metadata, reader.metadata)
        # content
        content = next(reader)
        check_consistency(expected_content, content)


@pytest.mark.parametrize("expected_metadata, expected_content, file_path",
                         zip(metadata_ls, content_ls, file_path_ls))
def test_writer_1(expected_metadata, expected_content, file_path):
    """
        测试以 writer.write_metadata() 的方式写入
            可以省略 writer.metadata_begin()/end() 和 writer.contents_begin()/end()
    """
    print("test Writer")

    # 新建
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test_data/temp",
                             os.path.basename(file_path))
    part = np.random.randint(1, 4)
    values = list(zip(*[expected_content[key][:-part] for key in expected_metadata["column_name"]]))
    with kevin_notation.Writer(file_path=file_path, mode="w", sep=expected_metadata["sep"]) as writer:
        if part % 2 == 0:
            # 逐个写入
            for key, value in expected_metadata.items():
                writer.write_metadata(key=key, value=value)
        else:
            # 整体写入
            writer.write_metadata(metadata=expected_metadata)

        # 列表方式写入
        #   多行写入
        writer.write_contents(row_ls=values[:-1], b_single_line=False)
        #   单行写入
        writer.write_contents(row_ls=values[-1], b_single_line=True)

    # 续写
    # 字典方式写入
    #   多行写入
    values = {k: v[-part:-1] for k, v in expected_content.items()}
    with kevin_notation.Writer(file_path=file_path, mode="a") as writer:
        writer.write_contents(column_dict=values, b_single_line=False)
    #   单行写入
    values = {k: v[-1] for k, v in expected_content.items()}
    with kevin_notation.Writer(file_path=file_path, mode="a") as writer:
        writer.write_contents(column_dict=values, b_single_line=True)

    # 检验
    with kevin_notation.Reader(file_path=file_path, chunk_size=1000) as reader:
        # metadata
        check_consistency(expected_metadata, reader.metadata)
        # content
        content = next(reader)
        check_consistency(expected_content, content)


@pytest.mark.parametrize("expected_metadata, expected_content, file_path",
                         zip(metadata_ls, content_ls, file_path_ls))
def test_read(expected_metadata, expected_content, file_path):
    print("test read()")
    # 使用 file_path 读取
    metadata, content = kevin_notation.read(file_path=file_path)

    # 使用 file_obj 读取
    file_obj = open(file_path, "r")
    metadata_1, content_1 = kevin_notation.read(file_obj=file_obj)
    assert len(file_obj.read()) > 0  # 不影响输入的 file_obj

    # 使用字符串构造 file_obj 读取
    from io import StringIO
    file_obj = StringIO(initial_value=open(file_path, "r").read())
    metadata_2, content_2 = kevin_notation.read(file_obj=file_obj)
    assert len(file_obj.read()) > 0

    # 检验
    check_consistency(expected_metadata, metadata, metadata_1, metadata_2)
    check_consistency(expected_content, content, content_1, content_2)


@pytest.mark.parametrize("expected_metadata, expected_content, file_path",
                         zip(metadata_ls, content_ls, file_path_ls))
def test_write(expected_metadata, expected_content, file_path):
    print("test write()")

    # 新建
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test_data/temp", os.path.basename(file_path))

    # 列表方式写入
    kevin_notation.write(metadata=expected_metadata,
                         content=list(zip(*[expected_content[key] for key in expected_metadata["column_name"]])),
                         file_path=file_path)
    # 检验
    metadata, content = kevin_notation.read(file_path=file_path)
    check_consistency(expected_metadata, metadata)
    check_consistency(expected_content, content)

    # 字典方式写入
    kevin_notation.write(metadata=expected_metadata, content=expected_content, file_path=file_path)
    # 检验
    metadata, content = kevin_notation.read(file_path=file_path)
    check_consistency(expected_metadata, metadata)
    check_consistency(expected_content, content)
