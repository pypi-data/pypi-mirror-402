import subprocess
import time

"""
检查包
- 若超过指定的有效期，则卸载。
"""

DEFAULT_EXPIRATION_TIMESTAMP = 1e10


def check_validity_and_uninstall(package_name, expiration_timestamp=DEFAULT_EXPIRATION_TIMESTAMP):
    """
        检查当前机器时间是否超过 expiration_timestamp 指定的有效期，若超过则卸载 package_name 对应的库
    """
    cur_timestamp = time.time()

    b_success_uninstalled = False
    if cur_timestamp > expiration_timestamp:
        ex = subprocess.Popen(f'pip uninstall {package_name} --yes', shell=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
        out, _ = ex.communicate()
        msg = out.decode().strip()
        if ex.returncode == 0:
            b_success_uninstalled = True
    else:
        msg = "still within the validity period"

    res_s = dict(cur_timestamp=cur_timestamp, expiration_timestamp=expiration_timestamp,
                 b_success_uninstalled=b_success_uninstalled, msg=msg)
    return res_s


if __name__ == '__main__':
    import argparse

    out_parser = argparse.ArgumentParser(description='check_validity_and_uninstall')
    out_parser.add_argument('--package_name', type=str, required=True)
    out_parser.add_argument('--expiration_timestamp', type=float, required=False, default=DEFAULT_EXPIRATION_TIMESTAMP)
    out_parser.add_argument('--verbose', type=lambda x: bool(eval(x)), required=False, default=True)
    args = out_parser.parse_args().__dict__

    b_version = args.pop("verbose")

    res_s_ = check_validity_and_uninstall(**args)

    if b_version:
        for k, v in res_s_.items():
            print(f"{k}: {v}")
