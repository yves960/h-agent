import os

# 测试session命名功能
def create_session_name():
    return os.urandom(8).hex()