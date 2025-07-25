import streamlit as st
import pandas as pd
import os

from . import ToppicPage
from . import FeaturePage
from . import UserGuide
from . import UserGuide

from ..Utils.FileUtils import FileUtils
from ..Utils.ServerUtils import ServerControl
import json


class ReportPage():
    def __init__(self):
        self.language = st.session_state.get('language', "en")
        self.selected_file = None
        self.df = None
        self._load_locale() 

    def _load_locale(self):
        """加载本地化文本"""
        try:
            pages_dir = os.path.dirname(os.path.abspath(__file__))
            locale_dir = os.path.join(pages_dir, '..','..', 'i18n')  
            locale_path = os.path.join(locale_dir, f"{self.language}.json")
            with open(locale_path, "r", encoding="utf-8") as f:
                self.locale = json.loads(f.read())
        except FileNotFoundError:
            st.error(f"未找到本地化文件: {locale_path}\n请检查以下路径是否存在: {os.path.abspath(locale_dir)}")
            self.locale = {}
        except Exception as e:
            st.error(f"加载本地化文件时出错: {str(e)}\n文件路径尝试: {locale_path}")
            self.locale = {}


    def run(self):
        self._sidebar()
        if not st.session_state.get('user_select_file'):
            guide = UserGuide.UserGuide()
            guide.run()
        else:
            self.show_report_page()

    def _sidebar(self):
        """整合所有侧边栏组件"""
        with st.sidebar:
            # 主文件夹选择
            if st.session_state.get('user_select_file'):
                file_suffix = os.path.splitext(st.session_state['user_select_file'])[1]
                if file_suffix not in [".pptx", ".docx"]:
                    file_utils = FileUtils()
                    samples = file_utils.list_samples(st.session_state['user_select_file'])
                    
                    # 主样本选择
                    st.session_state["sample"] = st.selectbox(
                        self.locale.get("select_sample", "选择检测样品"), 
                        samples,
                        key="sample_selection"
                    )

    def show_report_page(self):
        # 判断HTML报告是否存在
        html_available = FileUtils.has_html_report(
            st.session_state['user_select_file'],
            st.session_state['sample']
        )
        st.session_state["html_available"] = html_available

        if html_available:
            self.html_path = FileUtils.get_html_report_path(
                st.session_state['user_select_file'],
                st.session_state['sample']
            )
            ServerControl.start_report_server(self.html_path)
        else:
            st.warning("未检测到HTML报告文件，未启动HTML服务。")
            self.html_path = None

        st.title("TDvis")
        def get_feature_files():
            return [
                FileUtils.get_file_path("_ms1.feature",selected_path=st.session_state['user_select_file'],sample_name=st.session_state['sample']),
                FileUtils.get_file_path("_ms2.feature",selected_path=st.session_state['user_select_file'],sample_name=st.session_state['sample'])
            ]
        feature_files = get_feature_files()
        #tab选择界面
        feature_tab,report_tab,toppic_tab,guide_tab = st.tabs([
            self.locale.get("feature_tab_label", "特征图谱"),
            self.locale.get("report_tab_label", "汇总信息"),
            self.locale.get("toppic_tab_label", "二级报告"),
            self.locale.get("guide_tab_label", "使用指南")
        ])
        with feature_tab:
            with st.container():
                feature = FeaturePage.Featuremap(self.locale)
                feature.run()        
        with report_tab:
            # 只在tab内输出统计
            if html_available:
                stat_lines = self._count_report_files_html()
            else:
                stat_lines = self._count_report_files()
            if stat_lines:
                for line in stat_lines:
                    st.markdown(line)
            if feature_files:
                self.selected_file = st.selectbox(self.locale.get("selec_feature_file","选择特征文件"), feature_files,key="feature_file")
            self.df = pd.read_csv(self.selected_file, sep='\t')
            self._display_data_grid()
        with toppic_tab:
            toppic=ToppicPage.ToppicShowPage(self.locale)
            toppic.run()
        with guide_tab:
            guide=UserGuide.UserGuide()
            guide.run()

    def _count_report_files_html(self):
        """有HTML报告时统计蛋白质/变体/特征数目，返回markdown行"""
        try:
            base_path = os.path.join(
                self.html_path,
                "toppic_proteoform_cutoff",
                "data_js"
            )
            target_folders = [
                ("proteins", self.locale.get("proteins", "蛋白")),
                ("proteoforms", self.locale.get("proteoforms", "变体")), 
                ("prsms", self.locale.get("prsms", "特征"))
            ]
            results = []
            for folder, display_name in target_folders:
                folder_path = os.path.join(base_path, folder)
                if os.path.exists(folder_path):
                    file_count = len([
                        f for f in os.listdir(folder_path) 
                        if os.path.isfile(os.path.join(folder_path, f))
                    ])
                    results.append(f" **{display_name}**: {file_count} {self.locale.get('units', '个')}")
                else:
                    results.append(f"{self.locale.get('folder_not_found_prefix', '⚠️')} {display_name}{self.locale.get('folder_not_found_suffix', '目录不存在')}")
            lines = [self.locale.get("sample_detected_prefix", "__本样品共检测到:__")]
            lines += results
            return lines
        except Exception as e:
            st.sidebar.error(self.locale.get("file_count_failed", "文件统计失败: ") + str(e))
            return []

    def _count_report_files(self):
        """统计HTML报告相关文件数量（无HTML时），返回markdown行"""
        try:
            proteoform_file = FileUtils.get_file_path("_ms2_toppic_proteoform_single.tsv", 
                                                     selected_path=st.session_state['user_select_file'], 
                                                     sample_name=st.session_state['sample'])
            prsm_file = FileUtils.get_file_path("_ms2_toppic_prsm_single.tsv", 
                                               selected_path=st.session_state['user_select_file'], 
                                               sample_name=st.session_state['sample'])
            results = []
            if proteoform_file and os.path.exists(proteoform_file):
                try:
                    with open(proteoform_file, 'r') as f:
                        empty_line_idx = None
                        for i, line in enumerate(f):
                            if not line.strip():
                                empty_line_idx = i
                                break
                    df_proteoform = pd.read_csv(
                        proteoform_file,
                        sep='\t',
                        skiprows=empty_line_idx + 1 if empty_line_idx is not None else 0,
                        header=0,
                        on_bad_lines='warn',
                        dtype=str,
                        engine='python',
                        quoting=3
                    ).dropna(how='all')
                    proteoform_count = len(df_proteoform)
                    results.append(f" **{self.locale.get('proteoforms', '变体')}**: {proteoform_count} {self.locale.get('units', '个')}")
                except Exception as e:
                    results.append(f"{self.locale.get('folder_not_found_prefix', '⚠️')} {self.locale.get('proteoforms', '变体')}{self.locale.get('folder_not_found_suffix', '统计失败')}: {str(e)}")
            else:
                results.append(f"{self.locale.get('folder_not_found_prefix', '⚠️')} {self.locale.get('proteoforms', '变体')}{self.locale.get('folder_not_found_suffix', '文件不存在')}")
            if prsm_file and os.path.exists(prsm_file):
                try:
                    with open(prsm_file, 'r') as f:
                        empty_line_idx = None
                        for i, line in enumerate(f):
                            if not line.strip():
                                empty_line_idx = i
                                break
                    df_prsm = pd.read_csv(
                        prsm_file,
                        sep='\t',
                        skiprows=empty_line_idx + 1 if empty_line_idx is not None else 0,
                        header=0,
                        on_bad_lines='warn',
                        dtype=str,
                        engine='python',
                        quoting=3
                    ).dropna(how='all')
                    feature_count = len(df_prsm)
                    results.append(f" **{self.locale.get('prsms', '特征')}**: {feature_count} {self.locale.get('units', '个')}")
                except Exception as e:
                    results.append(f"{self.locale.get('folder_not_found_prefix', '⚠️')} {self.locale.get('prsms', '特征')}{self.locale.get('folder_not_found_suffix', '统计失败')}: {str(e)}")
            else:
                results.append(f"{self.locale.get('folder_not_found_prefix', '⚠️')} {self.locale.get('prsms', '特征')}{self.locale.get('folder_not_found_suffix', '文件不存在')}")
            lines = [self.locale.get("sample_detected_prefix", "__本样品共检测到:__")]
            lines += results
            return lines
        except Exception as e:
            st.sidebar.error(self.locale.get("file_count_failed", "文件统计失败: ") + str(e))
            return []

    def _display_data_grid(self):
        """配置Streamlit原生表格显示"""
        # 获取本地化文本，若不存在则使用默认值
        current_file_text = self.locale.get("current_file", "**当前文件:** ")
        download_button_text = self.locale.get("download_button", "📥 下载选中文件")
        fullscreen_tip = self.locale.get("fullscreen_tip", '''提示：使用表格右上角的按钮可进行全屏查看''')
        
        st.markdown(f"{current_file_text} `{os.path.basename(self.selected_file)}`")
        # 文件下载按钮
        csv_data = self.df.to_csv(index=False, sep='\t').encode('utf-8')
        st.download_button(
            label=download_button_text,
            data=csv_data,
            file_name=os.path.basename(self.selected_file),
            mime='text/csv',
            key='btn_download_feature'
        )
        
        # 替换AgGrid为streamlit原生表格
        st.dataframe(
            self.df,
            height=600,
            use_container_width=True,
            hide_index=True
        )
        st.markdown(fullscreen_tip)
        
