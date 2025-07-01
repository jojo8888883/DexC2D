"""
日志模块，实现统一的日志记录功能
"""

import logging
import os
import sys
from datetime import datetime

class Logger:
    """日志管理类，提供统一的日志记录接口"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_level=logging.INFO, log_dir=None):
        """初始化日志记录器"""
        if self._initialized:
            return
            
        self._initialized = True
        self.log_level = log_level
        
        # 创建日志目录
        if log_dir:
            self.log_dir = log_dir
        else:
            self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
            
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # 创建基本的日志格式
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 配置根日志记录器
        self._setup_root_logger()
        
        # 存储已创建的日志记录器
        self.loggers = {}
    
    def _setup_root_logger(self):
        """设置根日志记录器"""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.formatter)
        root_logger.addHandler(console_handler)
        
        # 文件处理器
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"dexc2d_{timestamp}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(self.formatter)
        root_logger.addHandler(file_handler)
    
    def get_logger(self, name):
        """获取指定名称的日志记录器"""
        if name in self.loggers:
            return self.loggers[name]
            
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # 已经继承了根日志记录器的处理器，不需要重复添加
        
        self.loggers[name] = logger
        return logger
        
# 全局日志管理器
_logger_manager = None

def get_logger(name):
    """获取指定名称的日志记录器"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = Logger()
    return _logger_manager.get_logger(name) 