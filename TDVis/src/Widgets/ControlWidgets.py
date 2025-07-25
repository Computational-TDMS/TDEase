import streamlit as st
import tkinter as tk
from tkinter import filedialog
import uuid
import json
import os
from ..Utils.FileUtils import FileUtils  # Assuming FileUtils is in this path
from ..Widgets.FeatureLoader import FeatureLoader

class ControlWidgets:
    def __init__(self, locale: dict):
        self.locale = locale  # Accept localization dictionary
        column_map = {
            'feature': ['Feature_ID', 'Feature ID'],
            'mass': ['Monoisotopic_mass','Mass', 'Precursor_mz'],
            'start_time':['Start_time', 'Min_time'],
            'end_time':['End_time', 'Max_time'],
            'time': ['Apex_time', 'Retention_time', 'RT'],
            'intensity': ['Intensity', 'Height', 'Area']
        }
        self.FeatureLoader = FeatureLoader(column_map,locale)  # Initialize FeatureLoader with locale
        # 常用颜色池
        self.color_pool = [
            "#d62728","#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
        ]


    def featuremap_widgets(self):
        """Initialize and display Featuremap-related controls"""
        expander_text = self.locale.get("heatmap_settings_expander", "**热力图基本设置**")

        with st.expander(expander_text):
            # View type selector
            st.session_state.feature_state['view_type'] = st.selectbox(
                self.locale.get("view_type_label", "视图模式"),
                options=['2D', '3D'],
                index=0 if st.session_state.feature_state['view_type'] == '2D' else 1,
                key='view_type_selector'
            )

            # Intensity processing
            st.session_state.feature_state['log_scale'] = st.selectbox(
                self.locale.get("intensity_process", "强度处理方式"),
                options=['log10','None', 'log2', 'ln','sqrt'],
                index=['log10','None', 'log2', 'ln','sqrt'].index(st.session_state.feature_state['log_scale']),
                key='log_scale_selector'
            )

            # Pixel settings
            st.session_state.feature_state['binx'] = st.number_input(
                self.locale.get("x_pixel_label", "x 轴像素"),
                min_value=10, max_value=9999,
                value=st.session_state.feature_state['binx'],
                key='binx_input'
            )
            st.session_state.feature_state['biny'] = st.number_input(
                self.locale.get("y_pixel_label", "y 轴像素"),
                min_value=10, max_value=9999,
                value=st.session_state.feature_state['biny'],
                key='biny_input'
            )

            # Data limit controls
            st.session_state.feature_state['data_limit'] = st.number_input(
                self.locale.get("data_limit_label", "显示数据点数量"),
                min_value=100, max_value=9999,
                value=st.session_state.feature_state['data_limit'],
                help=self.locale.get("data_limit_help", "按照强度从高到低排序,显示最强的前n个点以清晰化其图像"),
                key='data_limit_input'
            )
            st.session_state.feature_state['data_ascend'] = st.checkbox(
                self.locale.get("data_ascend_label", "逆序排布"),
                value=st.session_state.feature_state['data_ascend'],
                key='data_ascend_checkbox'
            )

        # 样本管理区块
        with st.expander(f"**📊 {self.locale.get('sample_management', '样本管理')}**", expanded=False):
            samples = st.session_state.feature_state.get('samples', [])
            
            # 显示主样本信息
            if samples:
                main_sample = samples[0]
                st.markdown(f"**{self.locale.get('main_sample_info', '主样本信息')}**")
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"**{self.locale.get('name_label', '名称')}**: {main_sample.get('name', self.locale.get('unnamed', '未命名'))}")
                        st.markdown(f"**{self.locale.get('file_label', '文件')}**: {main_sample.get('file', self.locale.get('unselected', '未选择'))}")
                        if main_sample.get('rt_correction_enabled', False):
                            rt_info = f"RT: {main_sample.get('rt_correction_offset', 0.0)}"
                            if main_sample.get('rt_correction_func'):
                                rt_info += f" + {main_sample.get('rt_correction_func')}"
                            st.markdown(f"*{rt_info}*")
                        else:
                            st.markdown(f"*{self.locale.get('rt_correction_disabled', 'RT矫正: 未启用')}*")
                    with col2:
                        st.color_picker(
                            self.locale.get("sample_color", "样本颜色"),
                            value=main_sample.get('color', "#0000FF"),
                            key="main_sample_color",
                            on_change=lambda: self._update_sample_color(0)
                        )
                    with col3:
                        if st.button(self.locale.get("edit_button", "编辑"), key="edit_main_sample"):
                            st.session_state.editing_sample = 0
                st.markdown("---")
            
            # 显示当前样本列表（排除主样本）
            if len(samples) > 1:  # 只显示对比样本
                st.markdown(f"**{self.locale.get('comparison_sample_count', '当前对比样本数量: {count}').format(count=len(samples) - 1)}**")
                for idx, sample in enumerate(samples[1:], 1):  # 从索引1开始，跳过主样本
                    with st.container(border=True):
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        with col1:
                            st.markdown(f"**{self.locale.get('comparison_sample_label', '对比样本 {idx}').format(idx=idx)}**: {sample.get('name', self.locale.get('unnamed', '未命名'))}")
                            st.markdown(f"{self.locale.get('file_label', '文件')}: {sample.get('file', self.locale.get('unselected', '未选择'))}")
                            # 显示RT矫正状态
                            if sample.get('rt_correction_enabled', False):
                                rt_info = f"RT Calibration: {sample.get('rt_correction_offset', 0.0)}"
                                if sample.get('rt_correction_func'):
                                    rt_info += f" + {sample.get('rt_correction_func')}"
                                st.markdown(f"*{rt_info}*")
                            else:
                                st.markdown(f"*{self.locale.get('rt_correction_disabled', 'RT矫正: 未启用')}*", help=self.locale.get("rt_correction_disabled_help", "灰色表示RT矫正未启用"))
                        with col2:
                            st.color_picker(
                                self.locale.get("sample_color", "样本颜色"),
                                value=sample.get('color', "#0000FF"),
                                key=f"sample_color_{idx}",
                                on_change=lambda idx=idx: self._update_sample_color(idx)
                            )
                        with col3:
                            if st.button(self.locale.get("edit_button", "编辑"), key=f"edit_sample_{idx}"):
                                st.session_state.editing_sample = idx
                        with col4:
                            if st.button(self.locale.get("delete_button", "删除"), key=f"delete_sample_{idx}"):
                                # 计算实际的样本索引（跳过主样本）
                                actual_idx = idx  # 因为我们已经从samples[1:]开始，所以idx就是实际索引
                                samples.pop(actual_idx)
                                st.rerun()
            elif len(samples) == 1:
                st.markdown(f"**{self.locale.get('only_main_sample', '当前只有主样本，请添加对比样本')}**")
            else:
                st.markdown(f"**{self.locale.get('no_samples', '暂无样本，请添加样本')}**")
            
            # 添加新样本
            st.markdown(f"**{self.locale.get('add_new_sample', '➕ 添加新样本')}**")
            with st.container(border=True):
                # 检查是否需要清空输入框
                if st.session_state.get('clear_add_sample_inputs', False):
                    st.session_state.clear_add_sample_inputs = False
                    # 清空相关输入框
                    if 'add_sample_name_input' in st.session_state:
                        del st.session_state.add_sample_name_input
                    if 'add_sample_file_selector' in st.session_state:
                        del st.session_state.add_sample_file_selector
                    if 'add_sample_selector' in st.session_state:
                        del st.session_state.add_sample_selector
                    if 'add_sample_file_path' in st.session_state:
                        del st.session_state.add_sample_file_path
                    if 'add_rt_correction_enabled' in st.session_state:
                        del st.session_state.add_rt_correction_enabled
                    if 'add_rt_correction_offset' in st.session_state:
                        del st.session_state.add_rt_correction_offset
                    if 'add_rt_correction_func' in st.session_state:
                        del st.session_state.add_rt_correction_func
                
                col1, col2 = st.columns(2)
                with col1:
                    # 自动分配颜色
                    used_colors = [s.get('color') for s in samples if s.get('color')]
                    available_colors = [c for c in self.color_pool if c not in used_colors]
                    auto_color = available_colors[0] if available_colors else "#0000FF"
                    new_sample_color = st.color_picker(
                        self.locale.get("sample_color", "样本颜色"),
                        value=auto_color,
                        key="add_sample_color_picker"
                    )
                    # 新增：强度修正系数
                    new_sample_intensity_scale = st.number_input(
                        self.locale.get("intensity_scale_label", "强度修正系数 (建议1.0~10.0)"),
                        min_value=0.01,
                        max_value=100.0,
                        value=1.0,
                        step=0.01,
                        key="add_sample_intensity_scale"
                    )
                with col2:
                    # 文件选择
                    if 'authentication_role' in st.session_state:
                        if st.session_state.authentication_role == 'user':
                            df = FileUtils.query_files(st.session_state.authentication_username)
                            if not df.empty:
                                df = df.drop_duplicates(subset=['文件名'])
                                df.index = df.index + 1
                                new_sample_file = st.selectbox(
                                    self.locale.get("select_file", "选择文件"),
                                    df['文件名'],
                                    index=None,
                                    key="add_sample_file_selector"
                                )
                        else:
                            if st.button(self.locale.get("select_file", "选择文件"), key="select_new_file"):
                                selected_dir = self._open_directory_dialog()
                                if selected_dir:
                                    st.session_state.add_sample_file_path = selected_dir
                            new_sample_file = st.session_state.get('add_sample_file_path')
                    else:
                        if st.button(self.locale.get("select_file", "选择文件"), key="select_new_file"):
                            selected_dir = self._open_directory_dialog()
                            if selected_dir:
                                st.session_state.add_sample_file_path = selected_dir
                        new_sample_file = st.session_state.get('add_sample_file_path')
                    # 样本选择
                    new_sample_name_from_file = None
                    if new_sample_file:
                        sample_options = FileUtils.list_samples(new_sample_file)
                        new_sample_name_from_file = st.selectbox(
                            self.locale.get("select_sample", "选择样本"),
                            options=sample_options,
                            index=0,
                            key='add_sample_selector'
                        )
                    else:
                        new_sample_name_from_file = None
                # RT矫正设置 - 默认启用，两列布局
                st.markdown(f"**{self.locale.get('rt_correction_settings', 'RT矫正设置')}**")
                st.caption(self.locale.get("rt_correction_description", "RT矫正用于校正不同样本间的保留时间差异。函数矫正优先级高于常数偏移。"))
                
                col_rt1, col_rt2 = st.columns(2)
                with col_rt1:
                    rt_correction_func = st.text_input(
                        self.locale.get("custom_function", "自定义函数"),
                        value="",
                        placeholder=self.locale.get("custom_function_placeholder", "如: x + 0.5 或 1.2 * x"),
                        help=self.locale.get("rt_correction_function_help", "函数矫正优先级最高，如: x + 0.5 或 1.2 * x"),
                        key="add_rt_correction_func"
                    )
                with col_rt2:
                    rt_correction_offset = st.number_input(
                        self.locale.get("constant_offset", "常数偏移"),
                        value=0.0,
                        step=0.1,
                        format="%.2f",
                        help=self.locale.get("rt_correction_offset_help", "当未设置函数时使用的常数偏移"),
                        key="add_rt_correction_offset"
                    )
                
                # 默认启用RT矫正
                rt_correction_enabled = True
                # 添加按钮
                if st.button(self.locale.get("add_sample_button", "添加样本"), key="add_sample_button"):
                    if new_sample_file and new_sample_name_from_file:
                        new_sample = {
                            'name': new_sample_name_from_file,
                            'file': new_sample_file,
                            'color': new_sample_color,
                            'intensity_scale': new_sample_intensity_scale,
                            'rt_correction_enabled': rt_correction_enabled,
                            'rt_correction_offset': rt_correction_offset,
                            'rt_correction_func': rt_correction_func if rt_correction_func else None
                        }
                        samples.append(new_sample)
                        # 设置标志来清空输入框
                        st.session_state.clear_add_sample_inputs = True
                        st.rerun()
                    else:
                        st.error(self.locale.get("incomplete_sample_info", "请填写完整的样本信息"))
            
            # 样本编辑功能
            if 'editing_sample' in st.session_state and st.session_state.editing_sample is not None:
                editing_idx = st.session_state.editing_sample
                if editing_idx < len(samples):
                    sample = samples[editing_idx]
                    st.markdown(f"**{self.locale.get('edit_sample_title', '✏️ 编辑样本 {idx}').format(idx=editing_idx)}**")
                    with st.container(border=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            edited_name = st.text_input(
                                self.locale.get("sample_name", "样本名称"),
                                value=sample.get('name', ''),
                                key=f"edit_sample_name_{editing_idx}"
                            )
                            edited_color = st.color_picker(
                                self.locale.get("sample_color", "样本颜色"),
                                value=sample.get('color', "#0000FF"),
                                key=f"edit_sample_color_{editing_idx}"
                            )
                            # 添加强度矫正系数编辑
                            edited_intensity_scale = st.number_input(
                                self.locale.get("intensity_scale_label", "强度修正系数"),
                                min_value=0.01,
                                max_value=100.0,
                                value=sample.get('intensity_scale', 1.0),
                                step=0.01,
                                key=f"edit_intensity_scale_{editing_idx}"
                            )
                        with col2:
                            st.markdown(f"**{self.locale.get('rt_correction_settings', 'RT矫正设置')}**")
                            st.caption(self.locale.get("rt_correction_edit_description", "函数矫正优先级高于常数偏移"))
                            
                            edited_rt_func = st.text_input(
                                self.locale.get("custom_function", "自定义函数"),
                                value=sample.get('rt_correction_func', ''),
                                placeholder=self.locale.get("custom_function_placeholder", "如: x + 0.5 或 1.2 * x"),
                                help=self.locale.get("rt_correction_function_help", "函数矫正优先级最高，如: x + 0.5 或 1.2 * x"),
                                key=f"edit_rt_func_{editing_idx}",
                                on_change=self._on_rt_correction_change
                            )
                            edited_rt_offset = st.number_input(
                                self.locale.get("constant_offset", "常数偏移"),
                                value=sample.get('rt_correction_offset', 0.0),
                                step=0.1,
                                format="%.2f",
                                help=self.locale.get("rt_correction_offset_help", "当未设置函数时使用的常数偏移"),
                                key=f"edit_rt_offset_{editing_idx}",
                                on_change=self._on_rt_correction_change
                            )
                            
                            # 默认启用RT矫正
                            edited_rt_enabled = True
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(self.locale.get("save_button", "保存"), key=f"save_edit_{editing_idx}"):
                                sample['name'] = edited_name
                                sample['color'] = edited_color
                                sample['intensity_scale'] = edited_intensity_scale
                                sample['rt_correction_enabled'] = edited_rt_enabled
                                sample['rt_correction_offset'] = edited_rt_offset
                                sample['rt_correction_func'] = edited_rt_func if edited_rt_func else None
                                st.session_state.editing_sample = None
                                st.rerun()
                        with col2:
                            if st.button(self.locale.get("cancel_button", "取消"), key=f"cancel_edit_{editing_idx}"):
                                st.session_state.editing_sample = None
                                st.rerun()

        # Advanced color settings (existing code with state fixes)
        advanced_expander_text = self.locale.get("advanced_color_settings_expander", "**高级颜色设置**")
        with st.expander(advanced_expander_text):
            self.use_custom = st.checkbox(
                self.locale.get("custom_color_checkbox", "启用自定义配色"),
                value=st.session_state.color_config['use_custom'],
                key='use_custom_color'
            )
            st.session_state.color_config['use_custom'] = self.use_custom
            
            if self.use_custom:
                # Fix typo: custom_colgers -> custom_colors
                if not st.session_state.color_config['custom_colors'] or \
                len(st.session_state.color_config['custom_colors']) != st.session_state.color_config['nodes']:
                    st.session_state.color_config['custom_colors'] = [
                        [i/(st.session_state.color_config['nodes']-1), "#FFFFFF"] 
                        for i in range(st.session_state.color_config['nodes'])
                    ]

                # Node management buttons (existing code)
                cols = st.columns([1,1,2])
                with cols[0]:
                    if st.button(self.locale.get("add_node_button","➕ 添加节点")) and st.session_state.color_config['nodes'] < 6:
                        st.session_state.color_config['nodes'] += 1
                        new_pos = min(1.0, st.session_state.color_config['custom_colors'][-1][0] + 0.2)
                        st.session_state.color_config['custom_colors'].append([new_pos, "#FFFFFF"])
                with cols[1]:
                    if st.button(self.locale.get("remove_node_button","➖ 减少节点")) and st.session_state.color_config['nodes'] > 2:
                        st.session_state.color_config['nodes'] -= 1
                        st.session_state.color_config['custom_colors'].pop()
                
                # Color pickers (existing code)
                updated_colors = []
                for i in range(st.session_state.color_config['nodes']):
                    with st.container(border=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            new_color = st.color_picker(
                                f"node {i+1} color",
                                value=st.session_state.color_config['custom_colors'][i][1],
                                key=f"color_{i}"
                            )
                        with col2:
                            new_pos = st.number_input(
                                f"node {i+1} position",
                                min_value=0.0, max_value=1.0,
                                value=st.session_state.color_config['custom_colors'][i][0],
                                step=0.01,
                                key=f"pos_{i}"
                            )
                        updated_colors.append([new_pos, new_color])
                
                st.session_state.color_config['custom_colors'] = updated_colors
                st.session_state.color_config['color_scale'] = [
                    [pos, color] for pos, color in sorted(updated_colors, key=lambda x: x[0])
                ]

    def integrate_widget(self):
        """Manual integration range controls"""
        with st.container():
            expander_title = self.locale.get("integration_manual_settings_expander", "**积分范围手动设置**")
            checkbox_label = self.locale.get("integration_manual_checkbox", "手动设置积分范围")
            checkbox_help = self.locale.get("integration_manual_help", "如果您对于Featuremap的框选范围不满意,可以手动设置积分范围。框选后启用")
            
            with st.expander(expander_title):
                manual = st.checkbox(checkbox_label, value=False, key='manual', help=checkbox_help)
                if manual:
                    # 获取当前样本数据
                    samples = st.session_state.feature_state.get('samples', [])
                    if samples:
                        # 使用第一个样本的数据
                        sample = samples[0]
                        df = self.FeatureLoader.load_sample_data(
                            sample.get('file'),
                            sample.get('name'),
                            sample.get('rt_correction_enabled', False),
                            sample.get('rt_correction_offset', 0.0),
                            sample.get('rt_correction_func')
                        )
                        if df is not None and not df.empty and 'mass' in df.columns and 'time' in df.columns:
                            mass_min0 = float(df['mass'].min())
                            mass_max0 = float(df['mass'].max())
                            time_min0 = float(df['time'].min())
                            time_max0 = float(df['time'].max())

                            col1, col2 = st.columns(2)
                            with col1:
                                # Mass range controls
                                st.session_state.feature_state['mass_range'] = (
                                    st.number_input(
                                        self.locale.get("mass_min_label", "积分质量下界"),
                                        min_value=mass_min0, max_value=mass_max0,
                                        value=mass_min0,
                                        format="%.6f",
                                        key='mass_min'
                                    ),
                                    st.number_input(
                                        self.locale.get("mass_max_label", "积分质量上界"),
                                        min_value=mass_min0, max_value=mass_max0,
                                        value=mass_max0,
                                        format="%.6f",
                                        key='mass_max'
                                    )
                                )
                            with col2:
                                # Time range controls
                                st.session_state.feature_state['time_range'] = (
                                    st.number_input(
                                        self.locale.get("time_min_label", "积分时间下界"),
                                        min_value=time_min0, max_value=time_max0,
                                        value=time_min0,
                                        format="%.6f",
                                        key='time_min'
                                    ),
                                    st.number_input(
                                        self.locale.get("time_max_label", "积分时间上界"),
                                        min_value=time_min0, max_value=time_max0,
                                        value=time_max0,
                                        format="%.6f",
                                        key='time_max'
                                    )
                                )
                        else:
                            st.error("无法获取样本数据或数据格式不正确")
                    else:
                        st.error("请先添加样本")


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

    def _update_sample_color(self, idx):
        """更新样本颜色"""
        samples = st.session_state.feature_state.get('samples', [])
        if idx < len(samples):
            samples[idx]['color'] = st.session_state.get(f"sample_color_{idx}")

    def _on_rt_correction_change(self):
        """Callback function for RT correction parameters."""
        # This function is called when any RT correction parameter changes.
        # It updates the session state and sets a flag for rerun.
        st.session_state.rerun_rt_correction = True
        # Note: Don't call st.rerun() in callbacks, let the page refresh naturally

