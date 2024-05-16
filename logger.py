import logging
from logging.handlers import TimedRotatingFileHandler
import os

# 创建颜色格式化器
class ColorFormatter(logging.Formatter):
    COLOR_CODES = {
        'DEBUG': '\033[94m',  # 蓝色
        'INFO': '\033[92m',  # 绿色
        'WARNING': '\033[93m',  # 黄色
        'ERROR': '\033[91m',  # 红色
        'CRITICAL': '\033[91m',  # 红色
        'RESET': '\033[0m'  # 重置颜色
    }

    def format(self, record):
        log_level = record.levelname
        log_message = super().format(record)
        color_code = self.COLOR_CODES.get(log_level, '')
        return f'{color_code}{log_message}{self.COLOR_CODES["RESET"]}'

def setup_logger(log_file,logger_name="app"):
    if not os.path.exists("log"):
        os.makedirs("log", exist_ok=True)

    # config = read_yaml("config.yaml")
    # 创建日志记录器
    # log_file = config['base_path'] + "log/"+ log_file
    log_file =  "./log/"+ log_file
    logger = logging.getLogger(logger_name)   
    logger.setLevel(logging.DEBUG)

    # 创建文件处理器
    #file_handler = logging.FileHandler(log_file)
    file_handler = TimedRotatingFileHandler(log_file, when='midnight', backupCount=30,encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # 创建日志格式器
    formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - %(filename)s:%(lineno)d => %(message)s')
    file_handler.setFormatter(formatter)

    color_formatter = ColorFormatter('[%(asctime)s] - %(levelname)s - %(filename)s:%(lineno)d => %(message)s')
    console_handler.setFormatter(color_formatter)
    #console_handler.setFormatter(formatter)

    # 将文件处理器和控制台处理器添加到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

