import os
import streamlit as st
import pandas as pd
from .Args import Args
from ..DBUtils import DBUtils

class FileUtils:
    """_summary_
    文件查询工具,用于统一维护文件查询路径
    可以查询用户名下对应的文件地址
    """

    @staticmethod
    def _resolve_path(input_path):
        """增强版路径解析，兼容本地和云端环境"""
        if not input_path:
            return None
            
        # 通过环境变量判断是否在Streamlit Cloud运行
        is_cloud = os.environ.get("IS_STREAMLIT_CLOUD", "false").lower() == "true"
        
        # 获取项目根目录
        if is_cloud:
            # 云端环境固定路径
            project_root = "/mount/src/tdvis_demo"
        else:
            # 本地环境动态计算
            current_script_path = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
        
        # 处理路径拼接
        resolved_path = os.path.join(project_root, input_path) if not os.path.isabs(input_path) else input_path
        return os.path.normpath(resolved_path)
    
    @staticmethod
    def list_samples(selected_path=None):

        resolved_path = FileUtils._resolve_path(selected_path or st.session_state.get('user_select_file'))

        if not resolved_path or not os.path.exists(resolved_path):
            raise FileNotFoundError(f"路径不存在: {resolved_path}")

        samples = []
        for filename in os.listdir(resolved_path):
            if filename.endswith("ms1.feature"):
                last_underscore_idx = filename.rfind("_")
                sample_name = filename[:last_underscore_idx] if last_underscore_idx != -1 else filename
                samples.append(sample_name)
        return samples

    @staticmethod
    def get_html_report_path(selected_path=None, sample_name=None):
        # 添加路径解析
        resolved_path = FileUtils._resolve_path(selected_path or st.session_state.get('user_select_file'))
        # 新增路径存在性检查
        if not resolved_path or not os.path.exists(resolved_path):
            raise FileNotFoundError(f"路径不存在: {resolved_path}")
            
        target_folder = f"{sample_name}_html"  # 名称构造逻辑
        # 遍历目录并检查是否为文件夹
        for entry in os.scandir(resolved_path):
            if entry.is_dir() and entry.name == target_folder:  # 精确匹配文件夹名称
                return os.path.join(resolved_path, entry.name)
        # raise FileNotFoundError(f"未找到HTML报告文件夹: {target_folder}")


    @staticmethod
    def get_file_path(suffix, selected_path=None, sample_name=None):
        # 确保使用解析后的路径
        resolved_path = FileUtils._resolve_path(selected_path or st.session_state.get('user_select_file'))
        # 新增路径校验
        if not resolved_path or not os.path.exists(resolved_path):
            raise FileNotFoundError(f"路径不存在: {resolved_path}")

        target_suffix = f"{sample_name}{suffix}"
        # 修复嵌套循环问题
        for filename in os.listdir(resolved_path):
            if filename.endswith(target_suffix):
                return os.path.join(resolved_path, filename)
        raise FileNotFoundError(f"未找到指定后缀文件: {target_suffix}")

    @staticmethod
    def has_html_report(selected_path=None, sample_name=None):
        """
        判断指定样本的HTML报告是否存在（包括文件夹和index.html）
        """
        html_dir = FileUtils.get_html_report_path(selected_path, sample_name)
        if not html_dir:
            return False
        html_index = os.path.join(html_dir, "topmsv", "index.html")
        return os.path.exists(html_index)


#  用户管理查询代码
    @staticmethod
    def query_files(username=None):
        """
        通用文件**地址**查询方法
        是为数据库操作
        :param username: 指定用户名时查询单个用户,None时查询所有用户
        :return: 包含(用户名, 文件名)的DataFrame
        """
        args = Args()  
        db_utils = DBUtils(args)  # 显式调用类名

        if username:
            file_addresses = db_utils.get_file_addresses(username)
            return pd.DataFrame([
                {"用户名": username, "文件名": os.path.normpath(f)}
                for f in file_addresses
            ])

        # 处理全部用户查询（管理员模式）
        all_files = []
        users = db_utils.query_users("", 0, 0)  # 获取所有用户
        for _, row in users.iterrows():
            file_addresses = db_utils.get_file_addresses(row['username'])
            all_files.extend([
                {"用户名": row['username'], "文件名": os.path.normpath(f)}
                for f in file_addresses
            ])
        return pd.DataFrame(all_files)

    @staticmethod  
    def query_user_files(username):
        """
        获取指定用户的文件列表
        设计数据库操作
        :param username: 当前登录用户名
        :return: 包含文件名的DataFrame(列名为file_name)
        """
        args = Args()  
        db_utils = DBUtils(args) 
        file_addresses = db_utils.get_file_addresses(username)
        return pd.DataFrame({'file_name': [os.path.normpath(f) for f in file_addresses]})

