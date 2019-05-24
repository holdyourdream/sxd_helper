import logging
from logging import handlers


class Logger(object):
    level_relations = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'crit': logging.CRITICAL
    }  # 日志级别关系映射

    def __init__(self, filename='../LOG/battle.log', level='debug', when='D', back_count=8, fmt='[%(asctime)s:%(message)s]'):
        self.logger = logging.getLogger(filename)

        # 实例化TimedRotatingFileHandler
        th = handlers.TimedRotatingFileHandler(filename=filename, when=when, backupCount=back_count, encoding='utf-8')
        # interval是时间间隔，backupCount是备份文件的个数，如果超过这个个数，就会自动删除，when是间隔的时间单位，单位有以下几种：
        # S 秒
        # M 分
        # H 小时
        # D 天
        # W 每星期（interval==0时代表星期一）
        # midnight 每天凌晨

        # 设置日志格式
        format_str = logging.Formatter(fmt)
        # 设置文件里写入的格式
        th.setFormatter(format_str)
        # 设置日志级别
        self.logger.setLevel(self.level_relations.get(level))
        # 往文件里写入#指定间隔时间自动生成文件的处理器
        self.logger.addHandler(th)
