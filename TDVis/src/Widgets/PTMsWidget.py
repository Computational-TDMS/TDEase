from ..Utils.ServerUtils import ServerControl
from ..Widgets.FeatureLoader import FeatureLoader
import streamlit as st
import pandas as pd
import uuid
import json
import socket  # 添加在已有的import区

class PTMsWidget:
    def __init__(self, locale=None):
        self.locale = locale
        # 同步独立PTMs列表
        self.ptms = [
                {"mass_diff": 15.994915, "name": "Oxidation"},
                {"mass_diff": 42.010565, "name": "Acetylation"},
            ]
        if 'ptms_list' not in st.session_state:
            st.session_state.ptms_list = [{'uuid': str(uuid.uuid4()), **item} for item in self.ptms]



    # 在PTMs_DIY方法的各个操作点添加状态更新标记
    def PTMs_DIY(self):
        """自定义PTMs质量差匹配规则"""
        # 保存原始状态用于变更检测
        original_ptms = [item.copy() for item in st.session_state.ptms_list] if 'ptms_list' in st.session_state else []
        
        # 初始化时从self.ptms同步到session_state
        if 'ptms_list' not in st.session_state:
            st.session_state.ptms_list = [{'uuid': str(uuid.uuid4()), **item} for item in self.ptms]
            
        # 获取本地化的展开器标题、按钮标签、输入标签和错误提示
        expander_title = self.locale.get("custom_ptms_expander", "**自定义PTMs匹配库**")
        add_button_label = self.locale.get("add_ptms_button", "➕ 添加PTMs规则")
        add_button_help = self.locale.get("add_ptms_help", "可以自定义修饰类型,比如将修饰进行组合后再查询")
        del_button_label = self.locale.get("del_ptms_button", "➖ 删除选中项")
        mass_diff_label = self.locale.get("mass_diff_label", "Mass Diff(Da)")
        ptms_type_label = self.locale.get("ptms_type_label", "PTMs Type")
        batch_input_button = self.locale.get("batch_input_button", "批量输入")
        parse_error = self.locale.get("parse_error", "解析失败: {0}，请确保输入格式为合法JSON数组")
        correct_format = '''正确输入格式:[{"mass_diff": 15.9949, "name": "氧化"}, 
{"mass_diff": 74.02100, "name": "乙酰化"}]'''
        ppm_threshold_label = self.locale.get("ppm_threshold_label", "匹配精度阈值 (ppm)")
        ppm_threshold_help = self.locale.get("ppm_threshold_help", "若精度高于该阈值,则认为超出质谱精度容忍范围,无匹配的修饰")
        
        # 保存原始的ppm阈值
        original_ppm = st.session_state.feature_state.get("ppm_threshold", 2)

        with st.expander(expander_title):
            # 在session_state中初始化PTMs存储
            if 'ptms_list' not in st.session_state:
                st.session_state.ptms_list = [{'uuid': str(uuid.uuid4()), **item} for item in self.ptms]
            col_add, col_del, _ = st.columns([1, 1, 3])
            with col_add:
                if st.button(add_button_label, help=add_button_help) and len(st.session_state.ptms_list) < 10:
                    st.session_state.ptms_list.append({"mass_diff": 0.0, "name": "", "uuid": str(uuid.uuid4())})
                    st.session_state.feature_state['ptms_updated'] = True  # 新增状态标记

            with col_del:
                if st.button(del_button_label) and len(st.session_state.ptms_list) > 1:
                    selected_indices = [i for i, item in enumerate(st.session_state.ptms_list) if st.session_state.get(f'del_{item["uuid"]}')]
                    if selected_indices:
                        for i in reversed(selected_indices):
                            del st.session_state.ptms_list[i]
                        st.session_state.feature_state['ptms_updated'] = True

            updated_entries = []
            for item in st.session_state.ptms_list:
                with st.container(border=True):
                    cols = st.columns([2, 2, 1])
                    with cols[0]:
                        new_mass = st.number_input(
                            mass_diff_label,
                            min_value=-1000.0,
                            value=item["mass_diff"],
                            step=0.00001,  # 步长缩小到1e-5
                            format="%.6f",  # 显示5位有效数字
                            key=f"ptms_mass_{item['uuid']}"
                        )
                    with cols[1]:
                        new_name = st.text_input(
                            ptms_type_label,
                            value=item["name"],
                            key=f"ptms_name_{item['uuid']}"
                        )
                    with cols[2]:
                        st.checkbox("delete", key=f"del_{item['uuid']}")
                updated_entries.append({"mass_diff": new_mass, "name": new_name, "uuid": item['uuid']})

            # 双向同步数据（session_state <-> self.ptms）
            st.session_state.ptms_list = updated_entries

            # 比较原始数据与修改后的数据
            if original_ptms != st.session_state.ptms_list:
                st.session_state.feature_state['ptms_updated'] = True

        with st.expander("**Batch Input**", expanded=False):
            ptm_text = st.text_area(self.locale.get("batch_input_PTMs", "批量输入PTMs规则"), value=correct_format, height=150, help=correct_format)
            if st.button(batch_input_button):
                try:
                    if ptm_text.strip():
                        new_ptms = json.loads(ptm_text)
                        # 转换所有mass_diff为float类型
                        for item in new_ptms:
                            item['mass_diff'] = float(item['mass_diff'])

                        st.session_state.ptms_list = [
                            {'uuid': str(uuid.uuid4()), **item}
                            for item in new_ptms
                        ]
                        st.session_state.feature_state['ptms_updated'] = True
                    st.success("批量输入成功")
                except Exception as e:
                    st.error(parse_error.format(str(e)))
                    st.json(correct_format)

            st.session_state.feature_state["ppm_threshold"] = st.number_input(
                ppm_threshold_label,
                min_value=0,
                max_value=20,
                value=original_ppm,
                help=ppm_threshold_help
            )

            # 检查ppm阈值是否改变
            if st.session_state.feature_state["ppm_threshold"] != original_ppm:
                st.session_state.feature_state['ptms_updated'] = True

    def request_feature_widget(self):
        """
        根据featureid来给出prsm的链接信息!
        """
        # 获取本地化文本
        expander_title = self.locale.get("prsm_query_expander", "**Prsm查询**")
        input_label = self.locale.get("featureid_input_label", "输入您感兴趣的FeatureID")
        input_help = self.locale.get("featureid_input_help", '会返回一个带有链接的表格,E-value越小,置信度越高')
        button_label = self.locale.get("prsm_query_button", "查询")
        no_prsm_info_warning = self.locale.get("no_prsm_info_warning", "未找到相关PrSM信息")
        prsm_link_column = self.locale.get("prsm_link_column", "prsm链接")
        prsm_link_help = self.locale.get("prsm_link_help", "点击查看详细prsm信息")

        with st.expander(expander_title, expanded=True):
            featureid = st.number_input("Feature ID", step=1, key='featureid', help=input_help)
            if st.button(button_label):
                prsmid = self._get_prsm_id(featureid)

                if prsmid.empty:
                    st.warning(no_prsm_info_warning)
                    return

                html_available = st.session_state.get("html_available", False)
                if html_available and 'URL' in prsmid.columns:
                    # 显示带链接
                    display_cols = ['URL'] + [col for col in [ 'E-value','Prsm ID', 'Scan(s)', 'Proteoform'] if col in prsmid.columns]
                    st.dataframe(
                        prsmid[display_cols],
                        column_config={
                            "URL": st.column_config.LinkColumn(
                                prsm_link_column,
                                help=prsm_link_help,
                                validate="^http",
                                max_chars=100
                            ),
                            "E-value": st.column_config.NumberColumn(
                                format="%.2e",
                                disabled=True
                            )
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    # 只显示 Prsm ID、Scan(s)、Proteoform、E-value
                    show_cols = [col for col in ['E-value','Prsm ID', 'Scan(s)', 'Proteoform',] if col in prsmid.columns]
                    st.dataframe(
                        prsmid[show_cols],
                        hide_index=True,
                        use_container_width=True
                    )

    def near_peak_widget(self, data):
        """邻近峰筛选控制（直接使用标准化列名）"""
        # 从feature_state获取状态
        selected_mass = st.session_state.feature_state['selected_mass']
        neighbor_range = st.session_state.feature_state['neighbor_range']
        neighbour_limit = st.session_state.feature_state['neighbour_limit']

        help_text = self.locale.get("near_peak_help", "邻近峰筛选是根据目标质量附近的峰来筛选的，筛选的范围由邻近峰质量范围和强度阈值控制。")

        unimod_text = self.locale.get("unimod_text", "Unimod是一个常用的PTMs修饰库,可以在这里查找常见的修饰")
        unimod_button_label = self.locale.get("unimod_button_label", "Unimod官网链接")

        exbasy_text = self.locale.get("exbasy_text", "📃可以使用exbasy工具来计算您目标蛋白的大致位置")
        exbasy_button_label = self.locale.get("exbasy_button_label", "exbasy:计算蛋白质精确质量")
        exbasy_tip = self.locale.get("exbasy_tip", "❗对于高分辨的质谱,需要在点击其中的Monoisotopic选项来计算")

        # 保存原始的邻近范围和强度阈值
        original_neighbor_range = neighbor_range
        original_neighbour_limit = neighbour_limit

        with st.expander(self.locale.get("near_peak_expander", " **邻近峰筛选:** 以框选区域强度最高的峰作为基准")):
            col1, col2 = st.columns(2)
            with col1:
                if not data.empty and 'mass' in data.columns:
                    current_min = float(data['mass'].min())
                    current_max = float(data['mass'].max())
                    clamped_value = min(max(float(selected_mass or 0), current_min), current_max)
                    manual_mass = st.number_input(
                        self.locale.get("manual_mass_label", "手动设置目标质量 (Da)"),
                        min_value=current_min,
                        max_value=current_max,
                        value=clamped_value,
                        key="manual_mass",
                        step=0.000001,
                        format="%.6f"
                    )
                    if manual_mass:
                        st.session_state.feature_state['selected_mass'] = manual_mass  # 更新feature_state

                # 更新feature_state中的邻近范围
                st.session_state.feature_state['neighbor_range'] = st.number_input(
                    self.locale.get("neighbor_range_label", "邻近峰质量范围(Da)"),
                    min_value=0.1,
                    max_value=10000.0,
                    value=neighbor_range,
                    step=0.1
                )

                # 更新feature_state中的强度阈值
                st.session_state.feature_state['neighbour_limit'] = st.number_input(
                    self.locale.get("intensity_threshold_label", "强度阈值控制(%)"),
                    min_value=0.00,
                    value=neighbour_limit,
                    max_value=100.00,
                    step=0.01
                )

            with col2:
                st.markdown(help_text)
                st.markdown(unimod_text)
                st.link_button(label=unimod_button_label, url="https://www.unimod.org/modifications_list.php?")
                st.markdown(exbasy_text)
                st.link_button(label=exbasy_button_label, url="https://web.expasy.org/compute_pi/")
                st.markdown(exbasy_tip)

        # 检查邻近范围和强度阈值是否改变
        new_neighbor_range = st.session_state.feature_state['neighbor_range']
        new_neighbour_limit = st.session_state.feature_state['neighbour_limit']
        if new_neighbor_range != original_neighbor_range or new_neighbour_limit != original_neighbour_limit:
            st.session_state.feature_state['ptms_updated'] = True

    def _get_prsm_id(self, ID):
        """根据featureID查询prsmID"""
        # 创建FeatureLoader实例
        column_map = {
            'feature': ['Feature_ID', 'Feature ID'],
            'mass': ['Monoisotopic_mass','Mass', 'Precursor_mz'],
            'start_time':['Start_time', 'Min_time'],
            'end_time':['End_time', 'Max_time'],
            'time': ['Apex_time', 'Retention_time', 'RT'],
            'intensity': ['Intensity', 'Height', 'Area']
        }
        loader = FeatureLoader(column_map, self.locale)
        
        # 修复参数顺序和名称
        df2 = loader.load_prsm_data(
            selected_path=st.session_state['user_select_file'],
            sample_name=st.session_state['sample'],  # 明确使用命名参数
        )
        if df2 is None or df2.empty:
            return pd.DataFrame()

        # 添加列名检查和类型转换
        feature_col = 'Feature ID'
        prsm_col = 'Prsm ID'
        scan_col = 'Scan(s)'
        proteoform_col = 'Proteoform'
        evalue_col = next((col for col in ['E-value', 'E_value', 'E Value'] if col in df2.columns), None)

        # 转换ID类型为与数据框一致
        try:
            matches = df2[df2[feature_col].astype(int) == int(ID)].copy()
        except KeyError:
            return pd.DataFrame()

        if matches.empty:
            return pd.DataFrame()

        # 确保Proteoform列为字符串类型
        if proteoform_col in matches.columns:
            matches[proteoform_col] = matches[proteoform_col].astype(str)

        # 选择需要的列
        required_cols = [col for col in [prsm_col, scan_col, proteoform_col, evalue_col] if col in matches.columns]
        result_df = matches[required_cols].copy()

        # 检查HTML是否可用，如果可用则添加URL列
        html_available = st.session_state.get("html_available", False)
        if html_available:
            # 添加获取本地IP的逻辑
            def get_local_ip():
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    return s.getsockname()[0]
                except Exception:
                    try:
                        return socket.gethostbyname(socket.gethostname())
                    except:
                        return "localhost"

            result_df['URL'] = result_df[prsm_col].apply(
                lambda x: f"http://{get_local_ip()}:8000/topmsv/visual/prsm.html?folder=../../toppic_prsm_cutoff/data_js&protein={x}"
            )

        return result_df
        
