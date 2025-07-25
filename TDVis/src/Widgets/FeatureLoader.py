import pandas as pd
import streamlit as st
import os
import numpy as np
from ..Utils.FileUtils import FileUtils


class FeatureLoader:
    '''
    功能：
        1. 加载特征数据
        2. 加载PrSM数据
        3. 列名标准化
        4. RT矫正
    直接从外部传入列名映射和本地化对象，从而确保解耦合

    '''
    def __init__(self, column_map,locale):
        self.locale = locale
        self.column_map = column_map

    def standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        识别并标准化数据框的列名
        
        Args:
            df: 原始数据框
            
        Returns:
            标准化列名后的数据框
        """
        if df is None or df.empty:
            return df
            
        # 列名映射规则
        column_map = {
            'feature': ['Feature_ID', 'Feature ID'],
            'mass': ['Monoisotopic_mass','Mass', 'Precursor_mz'],
            'start_time':['Start_time', 'Min_time'],
            'end_time':['End_time', 'Max_time'],
            'time': ['Apex_time', 'Retention_time', 'RT'],
            'intensity': ['Intensity', 'Height', 'Area']
        }
        
        # 创建列名映射字典
        rename_dict = {}
        for standard_name, possible_names in column_map.items():
            for col in df.columns:
                if col in possible_names:
                    rename_dict[col] = standard_name
                    break
        
        # 重命名列
        if rename_dict:
            df = df.rename(columns=rename_dict)
            
        return df

    def apply_rt_correction(self, df: pd.DataFrame, sample: dict) -> pd.DataFrame:
        """
        对数据框应用RT矫正
        
        Args:
            df: 原始数据框
            sample: 样本配置字典，包含RT矫正参数
            
        Returns:
            矫正后的数据框
        """
        if df is None or df.empty:
            return df
            
        # 检查是否启用RT矫正
        if not sample.get('rt_correction_enabled', False):
            return df
            
        # 获取时间列名（使用标准化的列名）
        time_cols = []
        for col_name in ['time', 'start_time', 'end_time']:
            if col_name in df.columns:
                time_cols.append(col_name)
        
        if not time_cols:
            return df
            
        # 创建数据框副本
        corrected_df = df.copy()
        
        # 应用RT矫正
        for time_col in time_cols:
            if time_col in corrected_df.columns:
                # 优先使用自定义函数
                if sample.get('rt_correction_func') is not None:
                    try:
                        # 这里可以扩展支持更复杂的函数表达式
                        # 目前支持简单的线性函数: a*x + b
                        func_str = sample['rt_correction_func']
                        if 'x' in func_str:
                            # 简单的函数求值（可以扩展为更安全的eval或ast.literal_eval）
                            corrected_df[time_col] = corrected_df[time_col].apply(
                                lambda x: eval(func_str, {"x": x, "np": np})
                            )
                    except Exception as e:
                        st.warning(f"RT矫正函数执行失败: {e}")
                        # 函数失败时回退到常数偏移
                        corrected_df[time_col] += sample.get('rt_correction_offset', 0.0)
                else:
                    # 使用常数偏移
                    corrected_df[time_col] += sample.get('rt_correction_offset', 0.0)
        
        return corrected_df

    @st.cache_data
    def load_sample_data(_self, file_path: str, sample_name: str, rt_correction_enabled: bool = False, rt_correction_offset: float = 0.0, rt_correction_func: str | None = None) -> pd.DataFrame:
        """
        加载、标准化列名并矫正样本数据
        
        Args:
            file_path: 文件路径
            sample_name: 样本名称
            rt_correction_enabled: 是否启用RT矫正
            rt_correction_offset: RT矫正常数偏移
            rt_correction_func: RT矫正自定义函数
            
        Returns:
            加载、标准化并矫正后的数据框
        """
        if not file_path or not sample_name:
            return pd.DataFrame()
        
        # 创建样本配置字典
        sample = {
            'file': file_path,
            'name': sample_name,
            'rt_correction_enabled': rt_correction_enabled,
            'rt_correction_offset': rt_correction_offset,
            'rt_correction_func': rt_correction_func
        }
        
        # 加载原始数据
        df = _self.load_feature_data(file_path, sample_name)
        
        # 标准化列名
        if df is not None and not df.empty:
            df = _self.standardize_columns(df)
            
            # 应用RT矫正
            df = _self.apply_rt_correction(df, sample)
            return df
        else:
            return pd.DataFrame()

    @st.cache_data
    def load_feature_data(_self, selected_path, sample_name):    
        feature_path = FileUtils.get_file_path('_ms1.feature', selected_path=selected_path, sample_name=sample_name)
        if not feature_path:
            error_text = _self.locale.get("feature_file_not_found", "❌ 未找到特征文件")
            st.error(error_text)
            return None
        
        try:
            df = pd.read_csv(feature_path, sep='\t')
            required_columns = _self.column_map['mass'] + _self.column_map['time']
            if not any(col in df.columns for col in required_columns):
                missing_cols = [col for col in required_columns if col not in df.columns]
                error_text = _self.locale.get("missing_required_columns", "❌ 缺少必要质量/时间列: {0}").format(', '.join(missing_cols))
                st.error(error_text)
                return None
            return df

        except Exception as e:
            error_text = _self.locale.get("feature_load_failed", "⛔ 特征数据加载失败: {0}").format(str(e))
            st.error(error_text)
            return None
    
    @st.cache_data
    def load_feature_data2(_self, selected_path, sample_name):    
        feature_path = FileUtils.get_file_path('_ms1.feature', selected_path=selected_path, sample_name=sample_name)
        if not feature_path:
            error_text = _self.locale.get("feature_file_not_found", "❌ 未找到特征文件")
            st.error(error_text)
            return None
        try:
            return pd.read_csv(feature_path, sep='\t')
        except Exception as e:
            error_text = _self.locale.get("feature_load_failed", "⛔ 特征数据加载失败: {0}").format(str(e))
            st.error(error_text)
            return None

    @st.cache_data
    def load_prsm_data(_self, selected_path, sample_name):
        """加载PrSM数据并缓存"""
        prsm_path = FileUtils.get_file_path('_ms2_toppic_prsm_single.tsv', selected_path=selected_path, sample_name=sample_name)
        if not prsm_path:
            error_text = _self.locale.get("prsm_file_not_found", "❌ 未找到PrSM数据文件")
            st.error(error_text)
            return None

        try:
            with open(prsm_path, 'r') as f:
                empty_line_idx = None
                for i, line in enumerate(f):
                    if not line.strip():
                        empty_line_idx = i
                        break

            return pd.read_csv(
                prsm_path,
                sep='\t',
                skiprows=empty_line_idx + 1 if empty_line_idx is not None else 0,
                header=0,
                on_bad_lines='warn',
                dtype=str,
                engine='python',
                quoting=3
            ).dropna(how='all')
        except pd.errors.EmptyDataError:
            error_text = _self.locale.get("prsm_file_empty", "文件 {0} 内容为空").format(os.path.basename(prsm_path))
            st.error(error_text)
            return None
        except Exception as e:
            error_text = _self.locale.get("prsm_load_failed", "加载 {0} 失败: {1}").format(os.path.basename(prsm_path), str(e))
            st.error(error_text)
            return None

    def load_data(self):
        """数据加载与校验（主方法）- 简化版，列名标准化在FeaturePage中处理"""
        selected_path = st.session_state['user_select_file']
        sample_name = st.session_state['sample']
        
        df = self.load_feature_data(selected_path, sample_name)
        df2 = self.load_prsm_data(selected_path, sample_name)

        if df is None or df2 is None:
            return False

        # 基础数据校验（列名标准化在FeaturePage中处理）
        required_columns = self.column_map['mass'] + self.column_map['time']
        if not any(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            error_text = self.locale.get("missing_required_columns", "❌ 缺少必要质量/时间列: {0}").format(', '.join(missing_cols))
            st.error(error_text)
            return False
            
        return True

    def load_data2(self):
        """数据加载与校验（对比样本）- 简化版"""
        selected_path = st.session_state['user_select_file2']
        sample_name = st.session_state['sample2']

        df = self.load_feature_data2(selected_path, sample_name)
        
        if df is None:
            return False
            
        # 基础数据校验
        required_columns = self.column_map['mass'] + self.column_map['time']
        if not any(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            error_text = self.locale.get("missing_required_columns", "❌ 缺少必要质量/时间列: {0}").format(', '.join(missing_cols))
            st.error(error_text)
            return False
        
        return True

    def find_column(self, candidates, df):
        """在数据框中查找候选列名（支持列名格式容错）"""
        for col in candidates:
            # 统一去除特殊字符后匹配
            normalized_col = col.replace(' ', '_').lower()
            for df_col in df.columns:
                if df_col.replace(' ', '_').lower() == normalized_col:
                    return df_col
        return None