import os
import logging


def build_logger(name, handler_ls, level=logging.DEBUG,
                 formatter="%(asctime)s - %(name)s - %(levelname)s - %(message)s", registry=None):
    """
        构建 logger，并注册到给定的 registry 空间中

        参数：
            name:               <str> 注册名称
            handler_ls:         <list of dict> 日志的输出方式
                                    其中每个 dict 应该包含以下字段
                                        - "target":     输出目标，当为 str 时表示输出文档路径，当为 None 时表示输出到控制台
                                        - "level":      捕获信息的级别
                                        - "formatter":  输出格式
                                    其中 "target" 是必须的，当 "level" 和 "formatter" 置空时，将从全局参数中获取
            level:              <int/str> （全局的）捕获信息的级别
                                    默认为 "DEBUG", 具体参看 logging 中的级别
            formatter:          <str> （全局的）输出格式
            registry:           <Registry> 注册空间
                                    默认不指定。
                                    当指定时，将尝试根据 name 从该空间中获取已有的 logger，或者创建后将新建的 logger 以 name 注册到该空间中。

                    !!注意：避免重复在多个空间中注册，难以管理，本函数所构建的 logger 将会从 logging 中的默认空间（logging.Logger.manager.loggerDict）
                            中删除。
    """
    if registry is not None:
        # 如果在 registry 中已存在，则不再创建，直接返回
        logger = registry.get(name=name, default=None)
        if logger is not None:
            return logger

    if len(handler_ls) == 0:
        return

    # 创建一个logger对象
    logger = logging.getLogger(name)
    logger = logging.Logger.manager.loggerDict.pop(name, logger)  # 从 logging 原生的管理器中删除注册记录，避免重复在多个空间中注册，难以管理
    logger.setLevel(logging.DEBUG)

    # 创建 handler，用于写入日志
    for details in handler_ls:
        if isinstance(details["target"], (str,)):
            # 输出到文件
            os.makedirs(os.path.dirname(details["target"]), exist_ok=True)
            handler = logging.FileHandler(details["target"])
        elif details["target"] is None:
            # 输出到控制台
            handler = logging.StreamHandler()
        else:
            raise ValueError(f'unexpected target {details["target"]}')
        temp = details.get("level", level)
        temp = getattr(logging, temp) if isinstance(temp, (str,)) else temp
        handler.setLevel(temp)
        handler.setFormatter(logging.Formatter(details.get("formatter", formatter)))
        # 添加到logger中
        logger.addHandler(handler)

    if registry is not None:
        # 将 logger 注册到 registry 中
        registry.add(obj=logger, name=name, b_force=False, b_execute_now=False)

    return logger
