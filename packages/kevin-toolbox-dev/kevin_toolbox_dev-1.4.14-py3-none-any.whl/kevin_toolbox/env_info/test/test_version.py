import pytest
from kevin_toolbox.env_info.version import compare, parse_to_array, sort_ls


@pytest.mark.parametrize("v_0, operator, v_1, kwargs, result",
                         [([1, 2, 3], ">=", [1, 3], dict(), False),
                          ([1, 2, 3], "<", [1, 3], dict(), True),
                          ([1, 2, 3], "==", [1, 2, 3, 0, 0], dict(), True),
                          ("1.10.0a0", ">", "1.2", dict(), True),
                          ("1.10.0a0", "<=", "1.2", dict(), False),
                          # 测试 sep
                          ("1.2.3", "<", [1, 3], dict(sep='.'), True),
                          ("n_7.3", "<", [1, 3], dict(sep='.'), True),
                          ("1_2_3", "==", "1_2_3_0_0", dict(sep='_'), True),
                          # 测试 mode
                          ("1_2_3", "==", "1_2_3_4_5", dict(sep='_', mode='short'), True), ])
def test_compare(v_0, operator, v_1, kwargs, result):
    assert compare(v_0, operator, v_1, **kwargs) == result


@pytest.mark.parametrize("string, sep, result",
                         [("1,2,3", ',', [1, 2, 3]),
                          ("1_2.3", '.', [-1, 3]),
                          ("neg", '_', [-1])])
def test_parse_to_array(string, sep, result):
    assert parse_to_array(string, sep=sep) == result


@pytest.mark.parametrize("inputs, expected",
                         [(dict(version_ls=["0.10.7", (0, 7), [0, 7, 5]], reverse=False),
                           [(0, 7), [0, 7, 5], "0.10.7"]),
                          (dict(version_ls=["0.10.7", (0, 7), [0, 7, 5]], reverse=True),
                           ["0.10.7", [0, 7, 5], (0, 7)]), ])
def test_sort_ls(inputs, expected):
    assert sort_ls(**inputs) == expected
