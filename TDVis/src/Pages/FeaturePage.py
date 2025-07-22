import streamlit as st
import plotly.graph_objects as go

import numpy as np
import pandas as pd

import io
import os
from ..Widgets.PTMsCalculator import PTMsCalculator
from ..Widgets.ControlWidgets import ControlWidgets
from ..Widgets.CalculateWidgets import CalculateWidgets
from ..Widgets.FeatureLoader import FeatureLoader
from ..Widgets.PTMsWidget import PTMsWidget

class Featuremap():
    def __init__(self, locale: dict) -> None:
        """初始化Featuremap类，设置基础参数和本地化配置"""
        self._init_session_state() 
        self._last_sync = None  # 修复linter报错，声明属性
        self._last_isotope_sync = None  # 声明同位素同步属性
        # 保留基础状态初始化

        column_map = {
            'feature': ['Feature_ID', 'Feature ID'],
            'mass': ['Monoisotopic_mass','Mass', 'Precursor_mz'],
            'start_time':['Start_time', 'Min_time'],
            'end_time':['End_time', 'Max_time'],
            'time': ['Apex_time', 'Retention_time', 'RT'],
            'intensity': ['Intensity', 'Height', 'Area']
        }
        #------对类进行实例化
        self.locale = locale
        self.control = ControlWidgets(locale)
        self.calculate = CalculateWidgets()
        self.loader=FeatureLoader(column_map,locale)
        self.PTMs=PTMsWidget(locale)
        self.PTMsCalculator = PTMsCalculator()  # Add unique key

    def _init_session_state(self):
        """初始化所有所需的session_state变量，支持多样本对比"""
        if 'feature_state' not in st.session_state:
            st.session_state.feature_state = {
                # 基础可视化设置
                'view_type': '2D',
                'log_scale': 'log10',
                'binx': 100,
                'biny': 100,
                'data_limit': 1000,
                'data_ascend': False,
                # 积分范围
                'time_range': None,
                'mass_range': None,
                # 多样本支持
                'samples': [],
                # PTMs分析
                'selected_mass': None,
                'neighbor_range': 200.0,
                'neighbour_limit': 3.00,
                'ptms_list': [{"mass_diff": 15.994915, "name": "Oxidation"},
                              {"mass_diff": 42.010565, "name": "Acetylation"}],
                'ppm_threshold': 2,
                'isotope_offsets':[0],
            }

        # 初始化color_config（如缺失）
        if 'color_config' not in st.session_state:
            st.session_state.color_config = {
                'use_custom': False,
                'nodes': 3,
                'custom_colors': [
                    [0.0, "#FF0000"], 
                    [0.5, "#0000FF"], 
                    [1.0, "#00FF00"]
                ],
                'color_scale': [[0.00, "#FFFFFF"], [0.4, "#0000FF"], [0.5, "#FF0000"], [1.00, "#FF0000"]]
            }

        # 自动填充样本（兼容老逻辑，已移除sample1_color/sample2_color相关）
        feature_state = st.session_state.feature_state
        if not feature_state['samples']:
            if st.session_state.get('user_select_file2') and st.session_state.get('sample2'):
                sample1 = {
                    'file': st.session_state.get('user_select_file'),
                    'name': st.session_state.get('sample'),
                    'color': "#0000FF",
                    'rt_correction_offset': 0.0,
                    'rt_correction_func': None,
                    'rt_correction_enabled': False
                }
                sample2 = {
                    'file': st.session_state.get('user_select_file2'),
                    'name': st.session_state.get('sample2'),
                    'color': "#FF0000",
                    'rt_correction_offset': 0.0,
                    'rt_correction_func': None,
                    'rt_correction_enabled': False
                }
                feature_state['samples'] = [sample1, sample2]
            else:
                sample1 = {
                    'file': st.session_state.get('user_select_file'),
                    'name': st.session_state.get('sample'),
                    'color': "#0000FF",
                    'rt_correction_offset': 0.0,
                    'rt_correction_func': None,
                    'rt_correction_enabled': False
                }
                feature_state['samples'] = [sample1]

    def run(self) -> None:
        """运行页面主逻辑"""
        self.showpage()

    @st.fragment()
    def showpage(self):  
        header_text = self.locale.get("ms1_featuremap_header", "**MS1 Featuremap**")
        st.markdown(header_text)
        
        # 同步侧边栏样本选择到feature_state
        self._sync_sidebar_sample()
        
        # 检查是否有样本数据
        samples = st.session_state.feature_state.get('samples', [])
        if not samples:
            st.warning("请先添加样本数据")
            return
            
        # 检查主样本数据是否可加载
        main_sample = samples[0]
        if not main_sample.get('file') or not main_sample.get('name'):
            st.warning("主样本数据不完整，请检查文件路径和样本名称")
            return
            
        # 尝试加载主样本数据
        df = self.loader.load_sample_data(
            main_sample.get('file'),
            main_sample.get('name'),
            main_sample.get('rt_correction_enabled', False),
            main_sample.get('rt_correction_offset', 0.0),
            main_sample.get('rt_correction_func')
        )
        if df is None or df.empty:
            st.error("无法加载主样本数据，请检查文件路径和样本名称")
            return
            
        featuremap_caption = self.locale.get("featuremap_caption", " :material/star: featrureMap:** 展示特征的时间和质量分布! 请在图中进行框选以进行下一步!")
        st.markdown(f'<div style="color:gray; font-size:1.1em">{featuremap_caption}</div>', unsafe_allow_html=True)
        with st.container(border=True):
            self.control.featuremap_widgets()
            self._plot_heatmap()
            
            # 只有在热力图中选中后才展示积分图谱
            if st.session_state.feature_state.get('time_range') and st.session_state.feature_state.get('mass_range'):
                # 本地化积分说明
                integration_caption = self.locale.get("integration_caption", " :material/star: **2.Integratation:** 对Featuremap进行积分，得到指定范围的质谱图,请在图中框选以进行下一步!")
                st.markdown(f'<div style="color:gray; font-size:1.1em">{integration_caption}</div>', unsafe_allow_html=True)
                with st.container(border=True):
                    # 多样本积分
                    integrated_datas = []
                    for idx, sample in enumerate(st.session_state.feature_state['samples']):
                        df = self.loader.load_sample_data(
                            sample.get('file'),
                            sample.get('name'),
                            sample.get('rt_correction_enabled', False),
                            sample.get('rt_correction_offset', 0.0),
                            sample.get('rt_correction_func')
                        )  # 使用FeatureLoader的统一接口
                        integrated_data = self.calculate.process_integration(df, sample)  # 传入样本配置以应用强度矫正
                        integrated_datas.append(integrated_data)
                    # 选中质量（主样本）
                    if integrated_datas[0] is None or integrated_datas[0].empty:
                        return
                    selected_mass = self._plot_spectrum_multi(integrated_datas)
                    st.session_state.feature_state['selected_mass'] = selected_mass

        # 只有有数据时才渲染PTMs
        if st.session_state.feature_state.get('selected_mass') is not None and 'integrated_datas' in locals() and integrated_datas[0] is not None and not integrated_datas[0].empty:
            # 本地化PTMs说明
            ptms_caption = self.locale.get("ptms_caption", " :material/star: **3.PTMs:** 对选定范围内最强的峰进行PTMs匹配!")
            st.markdown(f'<div style="color:gray; font-size:1.1em">{ptms_caption}</div>', unsafe_allow_html=True)
            with st.container(border=True):
                # 多样本PTMs匹配，全部以主样本selected_mass为基准
                ptms_data_list = []
                main_selected_mass = st.session_state.feature_state.get('selected_mass')
                for idx, integrated_data in enumerate(integrated_datas):
                    if integrated_data is not None and main_selected_mass is not None:
                        st.session_state.feature_state['selected_mass'] = main_selected_mass
                        neighbor = self.calculate.near_peak_process(integrated_data)
                        neighbor_diff = self.calculate.near_peak_match(neighbor)
                        ptms_data_list.append(neighbor_diff)
                    else:
                        ptms_data_list.append(pd.DataFrame())
                # 状态同步
                st.session_state.feature_state['ptms_data_list'] = ptms_data_list
                
                # 添加PTMs控制组件
                if integrated_datas[0] is not None and not integrated_datas[0].empty:
                    # 同步PTMs列表到feature_state
                    self._sync_ptms_list()
                    
                    self.PTMs.near_peak_widget(integrated_datas[0])

                    with st.expander("**PTMs Calculator**", expanded=False):
                        self.PTMsCalculator.PTMsCalculator()

                    self.PTMs.PTMs_DIY()

                    # 添加选中质量状态追踪
                    # 修改匹配条件检测逻辑
                    current_selected_mass = st.session_state.feature_state['selected_mass']
                    last_selected_mass = st.session_state.feature_state.get('last_selected_mass')
                    
                    # 新增状态检测参数
                    current_isotope = st.session_state.feature_state.get('isotope_offsets', [])
                    last_isotope = st.session_state.feature_state.get('last_isotope_offsets', [])
                    
                    # 扩展匹配条件检测范围
                    match_condition = (
                        current_selected_mass != last_selected_mass or 
                        st.session_state.feature_state.get('ptms_updated', False) or
                        current_isotope != last_isotope  # 检测同位素偏移变化
                    )
                    
                    # 修改匹配条件区块
                    if match_condition:
                        neighbor = self.calculate.near_peak_process(integrated_datas[0])  
                        self.neighbor_diff = self.calculate.near_peak_match(neighbor)
                        
                        # 增加状态变更检测
                        if not self.neighbor_diff.equals(st.session_state.feature_state.get('ptms_data', pd.DataFrame())):
                            st.session_state.feature_state['ptms_data'] = self.neighbor_diff.copy()
                            st.session_state.feature_state['last_isotope_offsets'] = current_isotope.copy()
                        
                        # 延后重置更新标记
                        st.session_state.feature_state['ptms_updated'] = False
                
                # 展示PTMs表格（有数据才渲染）
                if len(ptms_data_list) == 2:
                    col1, col2 = st.columns(2)
                    for idx, (col, ptms_data) in enumerate(zip([col1, col2], ptms_data_list)):
                        with col:
                            if ptms_data is not None and not ptms_data.empty:
                                st.markdown(f"**{self.locale.get('sample_ptms_result', '样本{idx+1} PTMs匹配结果').format(idx=idx+1)}**")
                                edited = st.data_editor(
                                    ptms_data.fillna(''),
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        "PTMS": st.column_config.TextColumn(
                                            help=self.locale.get("ptms_modification_help", "PTMs修饰类型")
                                        ),
                                        "Mass (Da)": st.column_config.NumberColumn(
                                            format="%.6f",
                                            help=self.locale.get("mass_help", "质量值")
                                        ),
                                        "Delta Mass(Da)": st.column_config.NumberColumn(
                                            format="%.6f",
                                            help=self.locale.get("delta_mass_help", "与基准峰的质量差")
                                        ),
                                        "ppm": st.column_config.NumberColumn(
                                            format="%.2f",
                                            help=self.locale.get("ppm_help", "匹配精度")
                                        ),
                                        "Isotopic Shift(Da)": st.column_config.TextColumn(
                                            help=self.locale.get("isotopic_shift_help", "同位素偏移")
                                        ),
                                        "Relative Intensity(%)": st.column_config.NumberColumn(
                                            format="%.2f",
                                            help=self.locale.get("relative_intensity_help", "相对强度百分比")
                                        ),
                                        "Feature ID": st.column_config.TextColumn(
                                            help=self.locale.get("feature_id_help", "特征ID")
                                        )
                                    },
                                    key=f"ptms_editor_{idx}"
                                )
                                st.session_state.feature_state['ptms_data_list'][idx] = edited
                elif len(ptms_data_list) == 4:
                    row1 = st.columns(2)
                    row2 = st.columns(2)
                    for idx, ptms_data in enumerate(ptms_data_list):
                        col = row1[idx] if idx < 2 else row2[idx-2]
                        with col:
                            if ptms_data is not None and not ptms_data.empty:
                                st.markdown(f"**{self.locale.get('sample_ptms_result', '样本{idx+1} PTMs匹配结果').format(idx=idx+1)}**")
                                edited = st.data_editor(
                                    ptms_data.fillna(''),
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        "PTMS": st.column_config.TextColumn(
                                            help="PTMs修饰类型"
                                        ),
                                        "Mass (Da)": st.column_config.NumberColumn(
                                            format="%.6f",
                                            help="质量值"
                                        ),
                                        "Delta Mass(Da)": st.column_config.NumberColumn(
                                            format="%.6f",
                                            help="与基准峰的质量差"
                                        ),
                                        "ppm": st.column_config.NumberColumn(
                                            format="%.2f",
                                            help="匹配精度"
                                        ),
                                        "Isotopic Shift(Da)": st.column_config.TextColumn(
                                            help="同位素偏移"
                                        ),
                                        "Relative Intensity(%)": st.column_config.NumberColumn(
                                            format="%.2f",
                                            help="相对强度百分比"
                                        ),
                                        "Feature ID": st.column_config.TextColumn(
                                            help="特征ID"
                                        )
                                    },
                                    key=f"ptms_editor_{idx}"
                                )
                                st.session_state.feature_state['ptms_data_list'][idx] = edited
                else:
                    for idx, ptms_data in enumerate(ptms_data_list):
                        if ptms_data is not None and not ptms_data.empty:
                            st.markdown(f"**{self.locale.get('sample_ptms_result', '样本{idx+1} PTMs匹配结果').format(idx=idx+1)}**")
                            edited = st.data_editor(
                                ptms_data.fillna(''),
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "PTMS": st.column_config.TextColumn(
                                        help="PTMs修饰类型"
                                    ),
                                    "Mass (Da)": st.column_config.NumberColumn(
                                        format="%.6f",
                                        help="质量值"
                                    ),
                                    "Delta Mass(Da)": st.column_config.NumberColumn(
                                        format="%.6f",
                                        help="与基准峰的质量差"
                                    ),
                                    "ppm": st.column_config.NumberColumn(
                                        format="%.2f",
                                        help="匹配精度"
                                    ),
                                    "Isotopic Shift(Da)": st.column_config.TextColumn(
                                        help="同位素偏移"
                                    ),
                                    "Relative Intensity(%)": st.column_config.NumberColumn(
                                        format="%.2f",
                                        help="相对强度百分比"
                                    ),
                                    "Feature ID": st.column_config.TextColumn(
                                        help="特征ID"
                                    )
                                },
                                key=f"ptms_editor_{idx}"
                            )
                            st.session_state.feature_state['ptms_data_list'][idx] = edited

                # 状态同步回调函数
                def sync_isotope_state():
                    if not hasattr(self, '_last_isotope_sync'):
                        self._last_isotope_sync = None
                    
                    current = st.session_state.feature_state['isotope_offsets']
                    if current != self._last_isotope_sync:
                        st.session_state.feature_state['ptms_updated'] = True
                        self._last_isotope_sync = current.copy()
                
                st.session_state.feature_state["isotope_offsets"] = st.multiselect(
                    self.locale.get("isotope_offsets_label", "选择允许的同位素偏移"),
                    options=[0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5],
                    default=st.session_state.feature_state.get("isotope_offsets", [0, 1, -1]),
                    key='feature_state.isotope_offsets',
                    on_change=sync_isotope_state
                )
                
                self.PTMs.request_feature_widget()

    def _sync_sidebar_sample(self):
        """同步侧边栏样本选择到feature_state"""
        # 检查侧边栏是否有样本选择
        if st.session_state.get('user_select_file') and st.session_state.get('sample'):
            samples = st.session_state.feature_state.get('samples', [])
            
            # 如果feature_state中没有样本，或者主样本与侧边栏选择不一致，则更新
            if not samples or samples[0].get('name') != st.session_state.get('sample'):
                # 更新主样本
                main_sample = {
                    'file': st.session_state.get('user_select_file'),
                    'name': st.session_state.get('sample'),
                    'color': st.session_state.feature_state.get('sample1_color', "#0000FF"),
                    'rt_correction_offset': 0.0,
                    'rt_correction_func': None,
                    'rt_correction_enabled': False
                }
                
                if not samples:
                    st.session_state.feature_state['samples'] = [main_sample]
                else:
                    st.session_state.feature_state['samples'][0] = main_sample

    def _sync_ptms_list(self):
        """同步PTMs列表到feature_state"""
        # 检查session_state中是否有ptms_list
        if 'ptms_list' in st.session_state:
            # 将session_state中的ptms_list同步到feature_state
            ptms_list = []
            for item in st.session_state.ptms_list:
                if isinstance(item, dict) and 'mass_diff' in item and 'name' in item:
                    ptms_list.append({
                        'mass_diff': float(item['mass_diff']),
                        'name': str(item['name'])
                    })
            
            # 更新feature_state中的ptms_list
            if ptms_list != st.session_state.feature_state.get('ptms_list', []):
                st.session_state.feature_state['ptms_list'] = ptms_list
                st.session_state.feature_state['ptms_updated'] = True

    def _add_ptms_annotations(self, fig, datas, is_mirror_mode, ptms_data_list=None):
        """在spectrum图表中添加PTMs标注，支持多样本"""
        samples = st.session_state.feature_state.get('samples', [])
        if ptms_data_list is None or not ptms_data_list or not samples:
            return
        for sample_idx, (sample, data, ptms_data) in enumerate(zip(samples, datas, ptms_data_list)):
            if ptms_data is None or ptms_data.empty or data is None or data.empty or 'mass' not in data.columns or 'intensity' not in data.columns:
                continue
            matched_ptms = ptms_data[ptms_data['PTMS'].notna() & (ptms_data['PTMS'] != '')]
            for idx, row in matched_ptms.iterrows():
                mass = row['Mass (Da)']
                ptms_name = row['PTMS']
                delta_mass = row.get('Delta Mass(Da)', 0)
                # 找到对应质量的峰
                mass_match = data[abs(data['mass'] - mass) < 0.01]  # 允许0.01的误差
                if mass_match.empty:
                    continue
                peak_intensity = mass_match['intensity'].iloc[0]
                max_intensity = data['intensity'].max()
                normalized_intensity = (peak_intensity / max_intensity) * 100 if max_intensity > 0 else 0
                # 计算标注位置
                if is_mirror_mode:
                    if sample_idx == 1:
                        y_pos = -normalized_intensity - 5
                        y_arrow = 20
                    else:
                        y_pos = normalized_intensity + 5
                        y_arrow = -20
                else:
                    y_pos = normalized_intensity + 5
                    y_arrow = -20
                sample_color = sample.get('color', '#0000FF')
                fig.add_annotation(
                    x=mass,
                    y=y_pos,
                    text=f"{ptms_name}<br>({delta_mass:+.3f})",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor=sample_color,
                    ax=0,
                    ay=y_arrow,
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor=sample_color,
                    borderwidth=2,
                    font=dict(size=10, color="black"),
                    name=f"PTMs_{sample_idx}_{mass:.3f}"
                )

    def _plot_heatmap(self):
        """支持多样本比对的3D/2D热图"""
        fig = go.Figure()
        state = st.session_state.feature_state
        samples = state['samples']
        num_samples = len(samples)
        data_list = []
        # 1. 加载所有样本数据
        for sample in samples:
            if sample.get('file') and sample.get('name'):
                df = self.loader.load_sample_data(
                    sample.get('file'),
                    sample.get('name'),
                    sample.get('rt_correction_enabled', False),
                    sample.get('rt_correction_offset', 0.0),
                    sample.get('rt_correction_func')
                )  # 使用FeatureLoader的统一接口
                if df is not None and not df.empty:
                    sorted_df = df.sort_values(
                        by='intensity',  # 使用标准化的列名
                        ascending=state['data_ascend']
                    ).head(state['data_limit'])
                else:
                    sorted_df = pd.DataFrame()
                data_list.append(sorted_df)
            else:
                data_list.append(pd.DataFrame())
        # 2. 绘制热力图
        if state["view_type"] == '3D':
            for idx, (sample, sorted_df) in enumerate(zip(samples, data_list)):
                if sorted_df.empty or 'mass' not in sorted_df.columns or 'time' not in sorted_df.columns or 'intensity' not in sorted_df.columns:
                    continue
                x = sorted_df["time"].values
                y = sorted_df["mass"].values
                z = self.calculate.apply_scale(sorted_df["intensity"])
                hist, xedges, yedges = np.histogram2d(np.asarray(x), np.asarray(y),
                    bins=(state['binx'], state['biny']),
                    weights=np.asarray(z))
                colorscale = [[0, '#FFFFFF'], [1, sample['color']]]
                fig.add_trace(go.Surface(
                    z=hist.T,
                    x=xedges,
                    y=yedges,
                    colorscale=colorscale,
                    hoverinfo='skip',
                    showscale=False,
                    opacity=0.7 if num_samples > 1 else 1.0
                ))
            fig.update_layout(
                scene=dict(
                    xaxis_title='Retention Time',
                    yaxis_title='Mass (Da)',
                    zaxis_title='Intensity',
                    camera=dict(eye=dict(x=1.5, y=1.5, z=0.5))
                ),
                margin=dict(l=0, r=0, b=0, t=30)
            )
        else:
            for idx, (sample, sorted_df) in enumerate(zip(samples, data_list)):
                if sorted_df.empty or 'mass' not in sorted_df.columns or 'start_time' not in sorted_df.columns or 'end_time' not in sorted_df.columns or 'intensity' not in sorted_df.columns:
                    continue
                fig.add_trace(go.Bar(
                    y=sorted_df["mass"],
                    x=sorted_df["end_time"] - sorted_df["start_time"],
                    base=sorted_df["start_time"],
                    orientation='h',
                    marker=dict(
                        color=sample['color'],
                        opacity=0.5 if num_samples > 1 else 0.3,
                        line=dict(width=0)
                    ),
                    hoverinfo='text',
                    width=1.6,
                    showlegend=True,
                    name=sample['name'] or f"样本{idx+1}"
                ))
            xaxis_title = self.locale.get("heatmap_xaxis_title", "Retention Time Range")
            yaxis_title = self.locale.get("heatmap_yaxis_title", "Mass (Da)")
            title = self.locale.get("heatmap_title", "Feature Heatmap")
            fig.update_layout(
                xaxis_title=xaxis_title,
                yaxis_title=yaxis_title,
                bargap=0.1,
                title=title,
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.2)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.2)'),
                hovermode='closest',
                dragmode='select',
            )
        event_data = st.plotly_chart(fig,
            key="feature_heatmap_multi",
            on_select="rerun",
            use_container_width=True,
            theme="streamlit",
            config={
                'modeBarButtonsToRemove': [
                    'toImage',
                    'lasso2d',
                    'plotlyLogo'
                ],
                'displayModeBar': True
            })
        col1, col2 = st.columns([1, 3])
        with col1:
            self._export_featuremap_html(fig)
        # 选择事件处理（只处理主样本，或可扩展多样本选区）
        if event_data["selection"]:
            try:
                box = next(b for b in event_data["selection"].get('box', []) if b.get('xref') == 'x' and b.get('yref') == 'y')
                time_min, time_max = sorted([box['x'][0], box['x'][1]])
                buffer = (time_max - time_min) * 0.05
                time_range = (time_min - buffer, time_max + buffer)
                mass_min, mass_max = sorted([box['y'][0], box['y'][1]])
                buffer = (mass_max - mass_min) * 0.05
                mass_range = (mass_min - buffer, mass_max + buffer)
                st.session_state.feature_state.update({
                    'time_range': time_range,
                    'mass_range': mass_range
                })
            except (StopIteration, KeyError, TypeError):
                pass
            except ValueError as e:
                error_text = self.locale.get("range_value_error", f"范围值错误: {str(e)}")
                st.error(error_text)

    def _plot_spectrum_multi(self, datas):
        """多样本积分图绘制，自动支持镜像与多色同向"""
        state = st.session_state.feature_state
        samples = state['samples']
        num_samples = len(samples)
        
        # 记录所有样本的mass范围
        if datas[0] is None or datas[0].empty:
            st.warning("当前积分范围内无数据")
            return None
            
        # 保存当前选中质量,避免状态被刷新!
        current_selected_mass = st.session_state.feature_state.get('selected_mass')
        
        # 判断是否为镜面模式（2个样本的镜像显示）
        is_mirror_mode = num_samples == 2
        
        # 创建图表
        fig = go.Figure()
        min_x, max_x = float('inf'), float('-inf')
        
        # 先计算主样本最大强度
        main_max_intensity = None
        if datas[0] is not None and 'intensity' in datas[0].columns:
            main_max_intensity = datas[0]['intensity'].max()
            if main_max_intensity == 0:
                main_max_intensity = 1.0  # 防止除零
        else:
            main_max_intensity = 1.0
        
        # 处理所有样本数据
        for idx, (sample, data) in enumerate(zip(samples, datas)):
            if data is None or 'mass' not in data.columns or 'intensity' not in data.columns:
                continue
            # 归一化
            data = data.copy()
            sample_max = data['intensity'].max()
            if sample_max == 0:
                sample_max = 1.0
            data['Normalized Intensity'] = data['intensity'] / sample_max * 100
            # 主样本直接100%，对比样本再乘以scale
            if idx == 0:
                y = data['Normalized Intensity']
            else:
                intensity_scale = sample.get('intensity_scale', 1.0)
                y = data['Normalized Intensity'] * intensity_scale
            # 镜面模式：第二个样本显示为负值
            if is_mirror_mode and idx == 1:
                y = -y
            fig.add_trace(go.Bar(
                x=data['mass'],
                y=y,
                marker=dict(
                    color=sample['color'],
                    opacity=0.7,
                    line=dict(width=0)
                ),
                name=sample['name'] or f"样本{idx+1}",
                hoverinfo='x+y',
                showlegend=True
            ))
            # 更新mass范围
            if not data['mass'].empty:
                min_x = min(min_x, data['mass'].min())
                max_x = max(max_x, data['mass'].max())
        # 根据模式设置Y轴
        if is_mirror_mode:
            self._setup_mirror_mode_layout(fig, min_x, max_x)
        else:
            self._setup_normal_mode_layout(fig)
        # 统一布局设置
        fig.update_layout(
            xaxis_title=self.locale.get("spectrum_xaxis_title", "质量 (Da)"),
            yaxis_title=self.locale.get("spectrum_yaxis_title", "强度(%)"),
            title=self.locale.get("spectrum_title", '积分图'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hoverdistance=30,
            dragmode='select',  # 始终启用框选模式
        )
        # 传入ptms_data_list
        ptms_data_list = st.session_state.feature_state.get('ptms_data_list', [])
        self._add_ptms_annotations(fig, datas, is_mirror_mode, ptms_data_list=ptms_data_list)
        # 渲染图表
        event_data = st.plotly_chart(fig,
            use_container_width=True,
            key="spectrum_multi",
            on_select="rerun",
            theme="streamlit",
            config={
                'modeBarButtonsToRemove': [
                    'toImage',
                    'lasso2d',
                    'plotlyLogo'
                ],
                'scrollZoom': True,
                'displayModeBar': True,
                'modeBarButtonsToAdd': ['autoScale2d']
            }
        )
        # 导出功能
        col1, col2 = st.columns([1, 3])
        with col1:
            self._export_spectrum_html(fig)
        # 处理框选事件
        return self._handle_selection_event(event_data, datas, is_mirror_mode, current_selected_mass)

    def _setup_mirror_mode_layout(self, fig, min_x, max_x):
        """设置镜面模式的Y轴布局"""
        fig.update_layout(
            yaxis=dict(
                tickvals=np.arange(-100, 101, 10),
                ticktext=[f"{abs(x)}" for x in np.arange(-100, 101, 10)],
                range=[-110, 110],
                tickmode='auto',
                nticks=22,
                autorange=True,
            )
        )
        # 添加镜像分隔线
        if min_x < max_x:
            fig.add_shape(
                type="line",
                x0=min_x,
                x1=max_x,
                y0=0,
                y1=0,
                line=dict(color="gray", width=2)
            )

    def _setup_normal_mode_layout(self, fig):
        """设置普通模式的Y轴布局"""
        fig.update_layout(
            yaxis=dict(
                tickvals=np.arange(0, 101, 10),
                range=[0, 110],
                tickmode='auto',
                nticks=12,
                autorange=True,
            )
        )

    def _debug_event_data(self, event_data):
        """调试输出事件数据"""
        pass

    def _handle_selection_event(self, event_data, datas, is_mirror_mode, current_selected_mass):
        """处理框选事件，支持多样本峰选择，主样本峰精确提取"""
        if isinstance(event_data, dict) and event_data.get("selection"):
            selection = event_data["selection"]
            points = selection.get("points", [])
            
            if not points:
                return current_selected_mass
                
            # 获取所有样本的峰信息
            samples = st.session_state.feature_state.get('samples', [])
            all_peaks = []
            for point in points:
                curve_number = point.get('curve_number', 0)
                if curve_number < len(samples):
                    sample = samples[curve_number]
                    mass = point.get('x')
                    intensity = abs(point.get('y', 0))  # 取绝对值，因为镜像模式可能是负值
                    # 应用强度矫正系数
                    intensity_scale = sample.get('intensity_scale', 1.0)
                    corrected_intensity = intensity * intensity_scale
                    all_peaks.append({
                        'sample_idx': curve_number,
                        'sample_name': sample.get('name', f'样本{curve_number+1}'),
                        'mass': mass,
                        'intensity': intensity,
                        'corrected_intensity': corrected_intensity
                    })
            if all_peaks:
                # 选择强度最高的峰
                max_peak = max(all_peaks, key=lambda p: p['corrected_intensity'])
                selected_mass = max_peak['mass']
                # 新增：回到主样本原始df，找±0.001 Da范围内最强峰
                main_sample = samples[0]
                df = self.loader.load_sample_data(
                    main_sample.get('file'),
                    main_sample.get('name'),
                    main_sample.get('rt_correction_enabled', False),
                    main_sample.get('rt_correction_offset', 0.0),
                    main_sample.get('rt_correction_func')
                )
                if df is not None and not df.empty and 'mass' in df.columns and 'intensity' in df.columns:
                    tol = 0.01
                    candidates = df[(df['mass'] >= selected_mass - tol) & (df['mass'] <= selected_mass + tol)]
                    if not candidates.empty:
                        intensity_col = pd.Series(candidates['intensity'])
                        strongest_idx = intensity_col.idxmax()
                        strongest = candidates.loc[strongest_idx]
                        selected_mass = strongest['mass']
                st.session_state.feature_state['selected_mass'] = selected_mass
                return selected_mass
            else:
                return current_selected_mass
        return st.session_state.feature_state.get('selected_mass')

    def _create_mirror_mode_mask(self, main_data, mass_min, mass_max, intensity_min, intensity_max):
        """创建镜面模式的数据筛选掩码"""
        if intensity_min < 0 and intensity_max < 0:
            # 负值区域，转换为正值进行匹配
            intensity_min_abs = abs(intensity_max)  # 注意：负值取绝对值后大小关系反转
            intensity_max_abs = abs(intensity_min)
            return (
                main_data['mass'].between(mass_min, mass_max) &
                main_data['Normalized Intensity'].between(intensity_min_abs, intensity_max_abs)
            )
        elif intensity_min < 0 and intensity_max > 0:
            # 跨越0线，需要分别处理
            return (
                main_data['mass'].between(mass_min, mass_max) &
                (main_data['Normalized Intensity'].between(0, intensity_max) |
                 main_data['Normalized Intensity'].between(abs(intensity_min), 100))
            )
        else:
            # 正值区域
            return (
                main_data['mass'].between(mass_min, mass_max) &
                main_data['Normalized Intensity'].between(intensity_min, intensity_max)
            )

    def _create_normal_mode_mask(self, main_data, mass_min, mass_max, intensity_min, intensity_max):
        """创建普通模式的数据筛选掩码"""
        return (
            main_data['mass'].between(mass_min, mass_max) &
            main_data['Normalized Intensity'].between(intensity_min, intensity_max)
        )

    # 兼容旧调用
    def _plot_spectrum(self, data):
        """兼容单样本/双样本调用，自动适配多样本"""
        state = st.session_state.feature_state
        samples = state['samples']
        datas = []
        if len(samples) == 1:
            datas = [data]
        else:
            # 兼容老逻辑，主样本用data，对比样本重新加载
            datas = [data]
            for idx in range(1, len(samples)):
                sample = samples[idx]
                df = self.loader.load_sample_data(
                    sample.get('file'),
                    sample.get('name'),
                    sample.get('rt_correction_enabled', False),
                    sample.get('rt_correction_offset', 0.0),
                    sample.get('rt_correction_func')
                )  # 使用FeatureLoader的统一接口
                datas.append(self.calculate.process_integration(df, sample))  # 传入样本配置以应用强度矫正
        return self._plot_spectrum_multi(datas)

    @st.fragment
    def _export_spectrum_html(self, fig):
        """HTML导出功能组件"""
        # 获取本地化的按钮标签
        button_label = self.locale.get("export_spectrum_button_label", "💾 导出交互式积分图")
        st.download_button(
            label=button_label,
            data=io.BytesIO(fig.to_html(
                include_plotlyjs="cdn",
                full_html=True
            ).encode('utf-8')).getvalue(),
            file_name="integrated_spectrum.html",
            mime="text/html",
            key="export_spectrum_html"
        )

    @st.fragment
    def _export_featuremap_html(self, fig):
        """HTML导出功能组件"""
        # 获取本地化的按钮标签
        button_label = self.locale.get("export_featuremap_button_label", "💾 导出交互式Featuremap")
        st.download_button(
            label=button_label,
            data=io.BytesIO(fig.to_html(
                include_plotlyjs="cdn",
                full_html=True
            ).encode('utf-8')).getvalue(),   
            file_name="featuremap.html",
            mime="text/html",
            key="export_featuremap_html")
