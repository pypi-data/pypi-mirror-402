import os
import time
import json
import hashlib
from enum import Enum
from kevin_toolbox.patches import for_os
from kevin_toolbox.data_flow.file import json_


class F_Type(Enum):
    file = 0
    symlink = 1
    dir = 2
    unknown = -1


class File_Feature_Extractor:
    """
        文件特征提取器类，用于扫描指定目录下所有文件（包括文件夹和符号链接），提取：
            - 文件元数据
            - 浅哈希值（仅支持对文件使用）
            - 完整哈希值等特征（仅支持对文件使用）
        并支持缓存、更新和持久化。

        参数：
            input_dir:                      <str> 根目录路径
            metadata_cfg:                   <dict> 提取元信息的方式。
                                                接受一个形如 {"attribute": ["size", ...], "include": ["file", ...], ...} 的字典，
                                                其中 "attribute" 字段下指定需要添加的元信息，目前支持：
                                                    - size 文件大小
                                                    - created_time、modified_time、accessed_time 时间
                                                    - mode 权限
                                                    - is_symlink、is_dir、is_file 种类
                                                    - is_symlink_valid 链接是否有效
                                                而 "include" 字段用于指定要遍历的目标类型。
                                                默认 "attribute" 和 "include" 均包含以上全部支持的选项。
                                                当设置为 None 时，表示不提取元信息。
            hash_cfg:                       <dict> 提取浅哈希的方式。
                                                接受形如 {"algorithm": ["md5", ...], "read_size": [<int>, None, ...], ...} 的字典
                                                其中 "algorithm" 表示使用的哈希算法类型，支持：
                                                    - 'md5', 'sha1', 'sha256'
                                                默认 "algorithm" 包含 "md5"。
                                                而 "read_size" 表示读取文件内容的最大前 N 个字节的内容来计算哈希值，支持：
                                                    - <int> 表示需要读取前 N 个字节
                                                    - None 表示读取整个文件
                                                默认 "read_size" 中的值为 [1024, None, ...]
            b_read_dst_of_symlink:          <boolean> 是否读取链接指向的目标文件。
                                                默认为 False。
            include:                        <list> 指定要遍历的目标类型
                                                当上面的 xxx_cfg 参数中没有额外指定 "include" 字段时，将以该参数作为该字段的默认参数。
                                                当给定值为 str 时，支持：
                                                    - "symlink"、"dir"、"file"
                                                当给定值为 dict 时，支持：
                                                    - {"filter_type": "suffix", "option_ls": [...]} 根据后缀进行选择。
                                                    - {"filter_type": "small_than", "size": <int>, "b_include_equal": <boolean>} 根据文件大小（单位为字节）选择。
                                                当给定值为函数时，函数应该形如：
                                                    - func(file_path) ==> <boolean>     当函数返回值为 True 时，表示匹配成功。
                                                另有一个特殊值为 None，表示匹配所有
            exclude:                        <list> 指定要排除的目标类型
                                                其设置参考 include。
                                                默认为 None，表示不排除任何
            walk_paras:                     <dict> 调用 for_os.walk() 对目录进行遍历时的参数
                                                利用该参数可以实现更高级的指定遍历顺序、排除内容的操作

        结果的形式：
            {
                <folder_A>:{
                    <folder_B>:{
                        (<base_name>, <type>):
                            {
                                "metadata": {"size": ..., ...},
                                "hash": {
                                    <size>: {"md5": ...., "sha": ...}
                                },
                                "dst_of_symlink": {"metadata": ...., "hash": ...}
                            }
                    }
                }
            }
            其中 type 有 "symlink"、"dir"、"file" None 几种取值

        方法：
            scan():                 扫描所有文件，提取特征并写入缓存
            update():               增量更新，只有当文件修改时间变化时才重新提取
            save_cache(file_path):   将当前缓存保存为 JSON 文件
            load_cache(file_path):   从 JSON 文件中加载缓存
    """

    def __init__(self, **kwargs):
        # 默认参数
        paras = {
            "input_dir": None,
            "metadata_cfg": {"attribute": {"size", "created_time", "modified_time", "accessed_time",
                                           "mode", "is_symlink", "is_dir", "is_file", "is_symlink_valid"}, },
            "hash_cfg": {"algorithm": {"md5", }, "read_size": {1024, None}, },
            "b_read_dst_of_symlink": False,
            "include": None,
            "exclude": None,
            "walk_paras": dict(topdown=True, onerror=None, followlinks=False, ignore_s=None)
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        if not paras["input_dir"] or not os.path.isdir(paras["input_dir"]):
            raise ValueError(f'invalid input_dir {paras["input_dir"]}')
        #
        for k in ["metadata_cfg", "hash_cfg"]:
            paras[k].setdefault('include', paras['include'])
            paras[k].setdefault('exclude', paras['exclude'])
        self.cache = {}
        self.paras = paras

    @staticmethod
    def _matches(path, rule_ls):
        """
            判断路径是否符合规则
        """
        path = os.path.realpath(path)
        stat = os.lstat(path)
        for rule in rule_ls:
            # 类型字符串匹配
            if isinstance(rule, str):
                if rule == 'file' and os.path.isfile(path): return True
                if rule == 'dir' and os.path.isdir(path): return True
                if rule == 'symlink' and os.path.islink(path): return True
                return False
            # 后缀过滤
            if isinstance(rule, dict):
                ft = rule.get('filter_type')
                if ft == 'suffix':
                    return any(path.endswith(suf) for suf in rule.get('option_ls', []))
                elif ft == 'small_than':
                    size = stat.st_size
                    limit = rule.get('size', 0)
                    eq = rule.get('b_include_equal', False)
                    return size < limit or (eq and size == limit)
            # 函数
            if callable(rule):
                return rule(path)
            return False
        return False

    @staticmethod
    def _get_metadata(path, attribute):
        """
            获取文件元信息
        """
        path = os.path.realpath(path)
        stat = os.lstat(path)
        res_s = dict()
        for attr in attribute:
            if attr == 'size': res_s['size'] = stat.st_size
            if attr == 'created_time': res_s['created_time'] = stat.st_ctime
            if attr == 'modified_time': res_s['modified_time'] = stat.st_mtime
            if attr == 'accessed_time': res_s['accessed_time'] = stat.st_atime
            if attr == 'mode': res_s['mode'] = stat.st_mode
            if attr == 'is_symlink': res_s['is_symlink'] = os.path.islink(path)
            if attr == 'is_dir': res_s['is_dir'] = os.path.isdir(path)
            if attr == 'is_file': res_s['is_file'] = os.path.isfile(path)
            if attr == 'is_symlink_valid':
                res_s['is_symlink_valid'] = os.path.islink(path) and os.path.exists(os.readlink(path))
        return res_s

    @staticmethod
    def _get_hash(path, read_size_ls, algorithm_ls):
        """
            对文件进行哈希，read_size=None 表示完整哈希，否则浅哈希
        """
        res_s = dict()
        for size in read_size_ls:
            for algo in algorithm_ls:
                h = hashlib.new(algo)
                with open(path, 'rb') as f:
                    if size is not None:
                        data = f.read(size)
                        h.update(data)
                    else:
                        for chunk in iter(lambda: f.read(8192), b''):
                            h.update(chunk)
                res_s[size] = res_s.get(size, dict())
                res_s[size][algo] = h.hexdigest()
        return res_s

    def extract_feature(self, path, metadata_cfg=None, hash_cfg=None):
        metadata_cfg = metadata_cfg or self.paras['metadata_cfg']
        hash_cfg = hash_cfg or self.paras['hash_cfg']
        path = os.path.realpath(path)
        res_s = dict()
        base_ = os.path.basename(path)
        if os.path.islink(path):
            f_type = F_Type.symlink
        elif os.path.isfile(path):
            f_type = F_Type.file
        elif os.path.isdir(path):
            f_type = F_Type.dir
        else:
            f_type = F_Type.unknown
        try:
            if metadata_cfg is not None:
                res_s["metadata"] = self._get_metadata(path, attribute=metadata_cfg['attribute'])
            if hash_cfg is not None and f_type == F_Type.file:
                res_s["hash"] = self._get_hash(path, read_size_ls=hash_cfg['read_size'],
                                               algorithm_ls=hash_cfg['algorithm'])
            if os.path.islink(path) and self.paras['b_read_dst_of_symlink']:
                dst = os.readlink(path)
                res_s['dst_of_symlink'] = self.extract_feature(dst)
        except Exception as e:
            res_s = {'error': str(e)}
        return base_, f_type.value, res_s

    def scan_path(self, path, metadata_cfg=None, hash_cfg=None):
        """
            扫描路径，提取特征并写入缓存
        """
        path = os.path.realpath(path)
        rel = os.path.relpath(path, self.paras["input_dir"])
        parts = rel.split(os.sep)
        node = self.cache
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        base_, f_type, res_s = self.extract_feature(path=path, metadata_cfg=metadata_cfg, hash_cfg=hash_cfg)
        node[(base_, f_type)] = res_s

    def scan_recursively(self, path=None, metadata_cfg=None, hash_cfg=None):
        """
            递归扫描目录，提取特征并写入缓存
        """
        path = path or self.paras["input_dir"]
        for root, dirs, files in for_os.walk(top=path, **self.paras["walk_paras"]):
            for name in files + dirs:
                full_path = os.path.join(root, name)
                if self.paras["include"] is not None:
                    if not self._matches(full_path, rule_ls=self.paras["include"]):
                        continue
                if self.paras["exclude"] is not None:
                    if self._matches(full_path, rule_ls=self.paras["exclude"]):
                        continue
                self.scan_path(full_path, metadata_cfg=metadata_cfg, hash_cfg=hash_cfg)

    def update(self):
        """
        增量更新，重新扫描修改过的文件
        """
        # 简化：重新全量扫描覆盖旧缓存，可按需优化
        self.cache.clear()
        self.scan_recursively()

    def save_cache(self, file_path):
        json_.write(content=self.cache, file_path=file_path, b_use_suggested_converter=True)

    def load_cache(self, file_path):
        self.cache = json_.read(file_path=file_path, b_use_suggested_converter=True)


if __name__ == '__main__':
    from kevin_toolbox.data_flow.file import markdown
    file_feature_extractor = File_Feature_Extractor(
        input_dir=os.path.join(os.path.dirname(__file__), "test/test_data")
    )
    file_feature_extractor.scan_recursively()
    print(markdown.generate_list(file_feature_extractor.cache))
