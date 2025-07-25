import streamlit as st
import pandas as pd
import os
from ..Utils.FileUtils import FileUtils  
from ..Utils.ServerUtils import ServerControl
import json


class ToppicShowPage():
    def __init__(self,locale):
        # 定义文件后缀映射
        # 定义文件后缀映射
        self.file_suffixes = {
            "Proteoform (Single)": "_ms2_toppic_proteoform_single.tsv",
            "Proteoform": "_ms2_toppic_proteoform.tsv",
            "PrSM": "_ms2_toppic_prsm.tsv",
            "PrSM (Single)": "_ms2_toppic_prsm_single.tsv"
        }
        
        # 配置各文件类型默认显示的列
        self.default_columns = {
            "_ms2_toppic_proteoform_single.tsv": ['Prsm ID', 'Precursor mass', 'Retention time','Fixed PTMs'],
            "_ms2_toppic_proteoform.tsv": ['Proteoform ID', 'Protein name', 'Mass'],
            "_ms2_toppic_prsm.tsv": ['PrSM ID', 'E-value', 'Score'],
            "_ms2_toppic_prsm_single.tsv": ['Feature ID', 'Sequence', 'Modifications']
        }
        # 加载本地化配置（假设与FeaturePage使用相同的本地化机制）
        self.language = st.session_state.get('language', "en")
        self.locale=locale

    def run(self):
        self.show_toppic()

    def _get_tsv_files(self):
        """扫描用户目录获取所有tsv文件并构建映射表"""
        selected_path = st.session_state['user_select_file']
        sample_name = st.session_state['sample']
        if not selected_path or not os.path.exists(selected_path):
            return None
        
        file_map = {}
        for suffix in self.file_suffixes.values():
            file_path = FileUtils.get_file_path(suffix, selected_path=selected_path, sample_name=sample_name)
            if file_path:
                file_map[suffix] = file_path
        return file_map

    def show_toppic(self):
        file_map = self._get_tsv_files()
        
        if not file_map:
            st.warning("未找到任何Toppic报告文件")
            return

        col = st.columns(2)
        
        with col[0]:
            # 替换为本地化标题
            st.write(self.locale.get("detailed_file_view", "**详细文件查看**"))
        with col[1]:
            # 移除HTML按钮，只保留标题
            st.write("")

        # 替换选项卡标题为本地化名称（假设file_suffixes的键已本地化）
        tab_titles = [ f"📊 {display_name}"  for display_name in self.file_suffixes.keys()]
        tabs = st.tabs(tab_titles)
        
        for idx, (display_name, suffix) in enumerate(self.file_suffixes.items()):
            with tabs[idx]:
                if file_map and suffix in file_map:
                    self._display_tab_content(file_map[suffix], suffix)
                else:
                    # 替换为本地化警告（支持文件名格式化）
                    warning_text = self.locale.get("file_type_not_found", "⚠️ 目录中未找到 {suffix} 类型的文件").format(suffix=suffix)
                    st.warning(warning_text)

    def _display_tab_content(self, file_path, suffix):
        # 动态检测空行位置（未修改）
        with open(file_path, 'r') as f:
            empty_line_idx = None
            for i, line in enumerate(f):
                if not line.strip():
                    empty_line_idx = i
                    break

        try:
            df = pd.read_csv(
                file_path,
                sep='\t',
                skiprows=empty_line_idx + 1 if empty_line_idx is not None else 0,
                header=0,
                on_bad_lines='warn',
                dtype=str,
                engine='python',
                quoting=3
            ).dropna(how='all')

            if df.empty:
                # 替换为本地化警告（支持文件名格式化）
                warning_text = self.locale.get("file_no_data", "文件 {filename} 无有效数据").format(filename=os.path.basename(file_path))
                st.warning(warning_text)
                return

            filename = os.path.basename(file_path)
            row_count = df.shape[0]
            # 替换为本地化条目数提示（支持数量格式化）
            count_text = self.locale.get("table_row_count", "✈ **表格条目数：** `{row_count:,}` 条").format(row_count=row_count)
            st.markdown(count_text)
            
            # 文件下载功能（替换按钮标签）
            download_label = self.locale.get("download_file", "📥 下载 {filename}").format(filename=filename)
            self._create_download_button(df, filename, download_label)
            
            # 表格显示配置（未修改）
            self._configure_aggrid(df, suffix, filename)
            
        except pd.errors.EmptyDataError:
            # 替换为本地化错误（支持文件名格式化）
            error_text = self.locale.get("file_empty", "文件 {filename} 内容为空").format(filename=os.path.basename(file_path))
            st.error(error_text)
        except Exception as e:
            # 替换为本地化错误（支持文件名和错误信息格式化）
            error_text = self.locale.get("file_load_failed", "加载 {filename} 失败: {error}").format(
                filename=os.path.basename(file_path), error=str(e)
            )
            st.error(error_text)


    def _create_download_button(self, df, filename, label):
        """创建下载按钮组件（新增label参数支持本地化）"""
        csv_data = df.to_csv(index=False, sep='\t').encode('utf-8')
        st.download_button(
            label=label,
            data=csv_data,
            file_name=filename,
            mime='text/tab-separated-values',
            key=f'download_{filename}'
        )

    def _configure_aggrid(self, df, suffix, filename):
        """配置Streamlit原生表格显示"""
        st.dataframe(
            df,
            height=600,
            use_container_width=True,
            hide_index=True
        )
        # 删除以下残留的AgGrid配置代码（已注释部分）
        # default_cols = self.default_columns[suffix]
        # grid_builder = GridOptionsBuilder.from_dataframe(df,enableValue=True,enableRowGroup=True,enablePivot=True)
        # for col in df.columns:
        #     grid_builder.configure_column(
        #         field=col,
        #         hide=col not in default_cols
        #     )
            
        # grid_builder.configure_side_bar(
        #     filters_panel=True, 
        #     columns_panel=True
        # )
        # AgGrid(
        #     df,
        #     gridOptions=grid_builder.build(),
        #     height=500,
        #     theme='streamlit',
        #     enable_enterprise_modules=True,
        #     custom_css={
        #         ".ag-header-cell-label": {"justify-content": "center"},
        #         ".ag-cell": {"display": "flex", "align-items": "center"}
        #     },
        #     key=f"grid_{filename}"
        # )