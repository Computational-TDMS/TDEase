from src import *

# Add missing imports at the top
import sys
import os
from streamlit.web import cli as stcli  # <-- Add this import
import traceback
import logging  # 新增日志模块

# 静默所有标准输出和错误输出
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

# 初始化日志配置
logging.basicConfig(
    filename='launch_error.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# 屏蔽Streamlit和依赖库的INFO/WARNING输出
logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime.caching.cache_data_api').setLevel(logging.ERROR)

def resolve_path(path):
    # 添加打包环境下的路径处理
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.getcwd()
    resolved_path = os.path.abspath(os.path.join(base_path, path))
    return resolved_path

if __name__ == "__main__":
    try:
        sys.path.insert(0, os.getcwd())
        # 关键修改：显式关闭开发模式（或移除端口参数）
        sys.argv = [
            "streamlit",
            "run",
            resolve_path("MainPage_web.py"),
            "--logger.level=error",
            "--global.developmentMode=false"  # 显式关闭开发模式
        ]
        exit_code = stcli.main()
        if exit_code != 0:
            raise RuntimeError(f"Streamlit exited with code {exit_code}")
    except Exception as e:
        error_msg = f"启动失败: {str(e)}"
        logging.error(error_msg, exc_info=True)
        print(error_msg)
        traceback.print_exc()
        os.system("pause")  # 更可靠的暂停方式
    finally:
        # 自动打开日志文件（仅限Windows）
        if os.path.exists('launch_error.log'):
            os.startfile('launch_error.log')