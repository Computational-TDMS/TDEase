import os
import streamlit as st
from src.Pages.ReportPage import ReportPage

import tkinter as tk
from tkinter import filedialog

class MainPage():
    def __init__(self):
        st.session_state.setdefault("language", "zh")
        
        # 清理可能存在的无效路径
        self._cleanup_invalid_paths()
    
    def _cleanup_invalid_paths(self):
        """清理session_state中可能存在的无效文件路径"""
        # 检查并清理无效的文件路径
        if "user_select_file" in st.session_state:
            file_path = st.session_state["user_select_file"]
            if not os.path.exists(file_path):
                st.warning(f"检测到无效的文件路径，已自动清理: {file_path}")
                st.session_state.pop("user_select_file", None)
        
        # 清理其他可能相关的无效路径
        invalid_keys = []
        for key in st.session_state.keys():
            if isinstance(st.session_state[key], str) and os.path.sep in st.session_state[key]:
                if not os.path.exists(st.session_state[key]):
                    invalid_keys.append(key)
        
        for key in invalid_keys:
            st.session_state.pop(key, None)

    def run(self):
        self.show_language_switcher()
        with st.sidebar:
            if st.button("📁", key="select_folder"):
                selected_dir = self._open_directory_dialog()
                if selected_dir:
                    # 验证选择的目录是否存在
                    if os.path.exists(selected_dir):
                        st.session_state["user_select_file"] = selected_dir
                        # 选择新文件夹时清除所有样本选择
                        st.session_state.pop("sample", None)
                        st.session_state.pop("sample2", None)
                    else:
                        st.error(f"选择的目录不存在: {selected_dir}")

        ReportPage().run()



    def show_language_switcher(self):
        # 添加语言切换下拉框
        with st.sidebar:
            lang = st.selectbox(
                "🌐 Language / 语言",
                ["zh", "en"],
            )
            # 保存用户选择的语言
            st.session_state["language"] = lang



    def _open_directory_dialog(self):
        """Open system directory dialog using Tkinter"""
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.wm_attributes('-topmost', 1)  # Add this line
        root.withdraw()
        
        # Force focus on the dialog
        root.update_idletasks()
        folder_path = filedialog.askdirectory(parent=root)
        
        # Cleanup
        root.destroy()
        
        return os.path.normpath(folder_path) if folder_path else None
            


if __name__ == "__main__":
    # 初始化streamlit运行时配置
    st.set_page_config(
        page_title="TDvis",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 初始化语言配置
    st.session_state.setdefault("language", "zh")
    main_page = MainPage()
    main_page.run()
