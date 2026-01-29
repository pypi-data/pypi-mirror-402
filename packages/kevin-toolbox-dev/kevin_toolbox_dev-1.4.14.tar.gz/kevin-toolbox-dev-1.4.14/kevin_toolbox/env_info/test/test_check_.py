import os
import pytest
from kevin_toolbox.env_info import check_validity_and_uninstall, check_version_and_update
from kevin_toolbox.patches.for_test import check_consistency


@pytest.mark.parametrize(
    "package_name, expiration_timestamp, expected_s",
    [
        ("tqdm", 1, {"b_success_uninstalled": True}),
        ("tqdm", 1e10, {"b_success_uninstalled": False}),
    ]
)
def test_check_validity_and_uninstall(package_name, expiration_timestamp, expected_s):
    # call by func
    res_s = check_validity_and_uninstall(package_name=package_name, expiration_timestamp=expiration_timestamp)
    print(res_s)
    for k, v in expected_s.items():
        check_consistency(res_s[k], v)

    # call by script
    os.system(
        f'python {os.path.dirname(os.path.split(__file__)[0])}/check_validity_and_uninstall.py ' +
        (f'--package_name {package_name} ' if package_name is not None else '') +
        (f'--expiration_timestamp {expiration_timestamp} ' if expiration_timestamp is not None else '') +
        f'--verbose 1'
    )


@pytest.mark.parametrize(
    "package_name, cur_version, available_versions, expected_s",
    [
        ("tqdm", None, None, {}),
        ("tqdm", "1.3.1", ["1.1.2", "1.1.3"], {"b_success_updated": False}),
    ]
)
def test_check_version_and_update(package_name, cur_version, available_versions, expected_s):
    # call by func
    res_s = check_version_and_update(package_name=package_name, cur_version=cur_version,
                                     available_versions=available_versions)
    print(res_s)
    for k, v in expected_s.items():
        check_consistency(res_s[k], v)

    # call by script
    os.system(
        f'python {os.path.dirname(os.path.split(__file__)[0])}/check_version_and_update.py ' +
        (f'--package_name {package_name} ' if package_name is not None else '') +
        (f'--cur_version {cur_version} ' if cur_version is not None else '') +
        (f'--available_versions {available_versions} ' if available_versions is not None else '') +
        f'--verbose 1'
    )