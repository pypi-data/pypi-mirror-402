from __future__ import annotations
import ast
import textwrap
import uuid
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
from pandas import Series


_link_in_setitem = True # FIXME: 临时方案
_link_in_getitem = True # FIXME: 临时方案
_accessed_cols = set()
_dataframes = {}  # pipe里全部mydataframe实例，格式{myid:mydf}


# FIXME: 临时方案，仅调试bug时使用
def reset_pipe():
    global _link_in_setitem, _link_in_getitem, _accessed_cols, _dataframes
    _link_in_setitem = True
    _link_in_getitem = True
    _accessed_cols = set()
    _dataframes = {}


class MyDataFrame(pd.DataFrame):

    # _metadata声明需要复制的属性
    # 这些属性值在__init__中的*args里（即data参数中）体现（主要是pandas内部copy的情况）
    # 见testcase中的test_copy_properties()
    _metadata = ['myid', 'actual_mappings', 'input_dfs','output_df', 'get_cols']

    def __init__(self, data=None, myid=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        if isinstance(data, MyDataFrame):
            # MyDataFrame(other_mydf)的情况
            if myid:
                self.myid = myid
                self.get_cols = set() # 用于记录哪些column被get访问过（使用过）
            else:
                self.myid = data.myid
                self.get_cols = data.get_cols

            # self.actual_mappings = data.actual_mappings
            # self.input_dfs = data.input_dfs
            # self.output_df = data.output_df

            # 无法获取到getitem的列联系，但胜在逻辑简单问题少
            self.actual_mappings = {}
            self.input_dfs = []
            self.output_df = None
        else:
            # MyDataFrame({...somedata...}) 或read_csv()的情况
            self.myid = myid or str(uuid.uuid4())
            self.actual_mappings = {}
            self.input_dfs = []
            self.output_df = None
            self.get_cols = set()

        _dataframes[self.myid] = self
        self.attrs['name'] = 'DataFrame'  # default name

    @property
    def _constructor(self):
        # 确保在 df 操作（如 df.head(), df.copy()）后仍返回 MyDataFrame 类型
        return MyDataFrame


    # 追溯 df[['col1','col2']] 这类filter操作
    def __getitem__(self, key):
        if isinstance(key, tuple):
            key = list(key)

        if isinstance(key, list):
            result = self.filter(key)
            result.attrs['op'] = 'getitem'
            return result

        if not isinstance(self, MyDataFrame):
            return super().__getitem__(key)

        # 为__setitem__时获取使用记录做准备
        if _link_in_getitem and isinstance(key, str):
            _accessed_cols.add(key)
            self.get_cols.add(key)

        # 其他key情况直接返回原始结果，不追溯：
        # slice类型：merge里会使用到此形式 left = self.left[:]
        # Series类型：drop_duplicate里使用
        # str类型：过于常用，例如df['k_ts'] = pd.to_datetime(df['k_ts'])
        # 可能还有其他类型
        return  super().__getitem__(key)


    # 追溯 df['new_col'] = df['col1'] + df['col2'] 这类操作
    def __setitem__(self, key, value):
        super().__setitem__(key, value)

        global _accessed_cols

        if not _link_in_setitem:
            _accessed_cols = set()
            return

        # 避免过于频繁的追溯记录
        if not isinstance(key, str):
            _accessed_cols = set()
            return

        # df['mycol] = 100 的情况，暂时处理方案
        if isinstance(value, int) or isinstance(value, str) or isinstance(value, float):
            self.actual_mappings.setdefault(key, set()).add((self.myid, str(value)))
            _accessed_cols = set()
            return

        if not (isinstance(value, Series)):
            _accessed_cols = set()
            return
        if key in ['k_ts', 'k_device']:
            _accessed_cols = set()
            return

        if not _accessed_cols:
            _accessed_cols = set()
            return

        # 流程图里不能新建df节点
        expression = ' * '.join(_accessed_cols)
        self.actual_mappings.setdefault(key, set()).add((self.myid, expression))

        _accessed_cols = set()

        # # FIXME: 无法创建新的MyDataFrame实例，仅用名称提示存在setitem操作
        # if self.name is None or 'set(' in self.name:
        #     return
        # self.name = self.name +f'\nset({key})'


    def join(self, right, on=None, **kwargs) -> MyDataFrame:
        result = super().join(right, on=on, **kwargs)
        assert isinstance(result, MyDataFrame) # DataFrame的join实际会通过concat完成，因此返回的是MyDataFrame
        result.attrs['op'] = 'join'
        return result


    def merge(self, right, on=None, **kwargs) -> MyDataFrame:
        # 目前不支持自动加_x、_y的处理
        # 如果两个df有同名列（on内除外），则抛出异常
        if on is None:
            raise ValueError("strict_merge 要求必须显式指定 [on](file://C:\k2data_workspace\k2pipe\.venv1\Lib\site-packages\pandas\core\reshape\merge.py#L720-L720) 参数。")

        # 标准化 on 为集合
        if isinstance(on, str):
            on_cols = {on}
        else:
            on_cols = set(on)

        # 检查 on 列是否都存在于两个 DataFrame 中
        missing_in_left = on_cols - set(self.columns)
        missing_in_right = on_cols - set(right.columns)
        if missing_in_left or missing_in_right:
            raise KeyError(
                f"连接键缺失：left 缺少 {missing_in_left}，right 缺少 {missing_in_right}"
            )

        # 检查是否存在非连接键的同名列
        common_cols = set(self.columns) & set(right.columns)
        extra_common = common_cols - on_cols

        # 如果存在非连接键的同名列，使用suffix参数处理
        suffixes = kwargs.get('suffixes', ('_x', '_y'))  # 默认后缀

        # 原始merge结果
        result = MyDataFrame(super().merge(on=on, right=right, **kwargs), myid=str(uuid.uuid4()))

        # 设置操作标识
        result.attrs['op'] = 'merge'

        # 处理列映射关系
        for col in self.columns:
            df_exp_pair = (self.myid, col)
            if col in extra_common:
                result.actual_mappings.setdefault(col + suffixes[0], set()).add(df_exp_pair)
            # elif col in on_cols:
            #     result.actual_mappings[col].add(tuple)
            else:
                result.actual_mappings.setdefault(col, set()).add(df_exp_pair)

        for col in right.columns:
            df_exp_pair = (right.myid, col)
            if col in extra_common:
                result.actual_mappings.setdefault(col + suffixes[1], set()).add(df_exp_pair)
            # elif col in on_cols:
            #     result.actual_mappings[col].add(df_exp_pair)
            else:
                result.actual_mappings.setdefault(col, set()).add(df_exp_pair)

        # 记录读取了哪些列
        for col in self.columns:
            self.get_cols.add(col)
        for col in right.columns:
            right.get_cols.add(col)

        # 建立连接关系
        result.input_dfs = [self, right]
        self.output_df = result
        right.output_df = result

        return result



    # 覆盖pd.DataFrame的rename方法
    def rename(self, inplace = None, *args, **kwargs) -> MyDataFrame:
        if inplace:
            raise ValueError("mydataframe.rename 暂不支持 inplace=True 参数") # TODO
        result = MyDataFrame(super().rename(*args, **kwargs), myid=str(uuid.uuid4()))
        result.attrs['op'] = 'rename'
        for old, new in zip(list(self.columns), list(result.columns)):
            result.actual_mappings.setdefault(new, set()).add((self.myid,old))
        # 记录读取了哪些列
        for col in self.columns:
            self.get_cols.add(col)
        # 建立连接关系
        result.input_dfs = [self]
        self.output_df = result
        return result


    # 覆盖pd.DataFrame的fitler方法
    def filter(self, *args, **kwargs) -> MyDataFrame:
        result = MyDataFrame(super().filter(*args, **kwargs), myid=str(uuid.uuid4()))
        result.attrs['op'] = 'filter'
        columns = _all_columns(result)
        for col in columns:
            result.actual_mappings.setdefault(col, set()).add((self.myid,col))
        # 记录读取了哪些列
        for col in result.columns:
            self.get_cols.add(col)
        # 建立连接关系
        result.input_dfs = [self]
        self.output_df = result
        return result

    # 追溯 df = df.assign(new_col = df['col1'] + df['col2'])
    def assign(self, **kwargs) -> MyDataFrame:
        df_result = super().assign(**kwargs)
        result = MyDataFrame(df_result, myid=str(uuid.uuid4()))

        result.attrs['op'] = 'assign'

        # assign会触发__setitem__，新col的映射关系是在__setitem__里创建的
        for col in self.columns:
            result.actual_mappings.setdefault(col, set()).add((self.myid,col))
        # FIXME: 记录读取了哪些列（逻辑需要确认）
        for col in self.columns:
            self.get_cols.add(col)
        # 建立连接关系
        result.input_dfs = [self]
        self.output_df = result
        return result


    # 覆盖pd.DataFrame的query方法
    def query(self, *args, **kwargs) -> MyDataFrame:
        result = MyDataFrame(super().query(*args, **kwargs), myid=str(uuid.uuid4()))
        # actual_mappings
        result.attrs['op'] = 'query'
        for col in result.columns:
            result.actual_mappings.setdefault(col, set()).add((self.myid,col))
        # 记录读取了哪些列
        for col in result.columns:
            self.get_cols.add(col)
        # 记录读取了哪些列（对query来讲这里的操作似乎重复，但因为是set所以没影响）
        for col in self.columns:
            self.get_cols.add(col)
        # 建立连接关系
        result.input_dfs = [self]
        self.output_df = result
        return result


    # mypipe内部应使用原始drop，以免产生多余的追溯
    def _original_drop(self, *args, **kwargs):
        return super().drop(*args, **kwargs)


    # 覆盖pd.DataFrame的drop方法
    def drop(self, *args, **kwargs) -> MyDataFrame:
        result = MyDataFrame(super().drop(*args, **kwargs), myid=str(uuid.uuid4()))
        result.attrs['op'] = 'drop'
        for col in result.columns:
            result.actual_mappings.setdefault(col, set()).add((self.myid,col))
        # 记录读取了哪些列（被drop掉的不包含在内）
        for col in result.columns:
            self.get_cols.add(col)
        # 建立连接关系
        result.input_dfs = [self]
        self.output_df = result
        return result


    # 覆盖pd.DataFrame的drop方法
    def dropna(self, *args, **kwargs) -> MyDataFrame:
        result = MyDataFrame(super().dropna(*args, **kwargs), myid=str(uuid.uuid4()))
        result.attrs['op'] = 'dropna'
        for col in result.columns:
            result.actual_mappings.setdefault(col, set()).add((self.myid,col))
        # 记录读取了哪些列
        for col in self.columns:
            self.get_cols.add(col)
        # 建立连接关系
        result.input_dfs = [self]
        self.output_df = result
        return result


    # 根据配置的映射信息进行批量化的列级操作，例如重命名、特征提取等
    def extract_features(self, config: Union [pd.DataFrame, str, Path], step_name: str = None) -> MyDataFrame:
        # 如果 config 是路径（Path 或 str），则读取为 DataFrame
        if isinstance(config, (str, Path)):
            config = pd.read_csv(config)
        elif not isinstance(config, pd.DataFrame):
            raise TypeError("config must be a pandas DataFrame, a string path, or a pathlib.Path object.")

        result = MyDataFrame(self, myid=str(uuid.uuid4())) # 不能用copy()创建新实例，会将actual_mappings等属性复制过来
        if step_name:
            result.attrs['name'] = step_name
        result.columns = result.columns.str.strip()  # 防止列名前后有空格造成难以排查的错误

        # 展开第一个 * 为所有列名，并放在最前面
        if '*' in config['feature'].values:
            config.drop(config[config['feature'] == '*'].index, inplace=True)
            new_df = pd.DataFrame(columns=config.columns)
            for col in list(self.columns):
                new_df.loc[len(new_df)] = {'feature':col, 'expression':col, 'comment':'*'}
            for idx, row in config.iterrows():
                new_df.loc[len(new_df)] = row
            config = new_df

        for _, row in config.iterrows():
            # 忽略注释行
            if row[0].startswith('#'):
                continue

            feature_name = row['feature']
            if not pd.isna(feature_name):
                feature_name = feature_name.strip()
            else:
                raise ValueError(f"特征名称不能为空 {row}, line: {_}")

            _validate_var_name(feature_name)

            expression = row['expression']
            if not pd.isna(expression):
                expression = expression.strip()
            else:
                result[feature_name] = np.nan
                continue

            # 避免触发__setitem__
            # FIXME: 建议改为 with () 包裹的方式
            global _link_in_setitem
            _link_in_setitem = False
            if feature_name == expression:
                # 非数值类型用eval容易报错，这种情况直接赋值
                result[feature_name] = result[expression]
                # 记录读取了哪些列
                self.get_cols.add(feature_name)  # FIXME: 区分self和result
            else:
                result[feature_name] = _eval(result, expression)
                # 记录读取了哪些列
                cols = _extract_column_names(expression)
                for col in cols:
                    self.get_cols.add(col)

            _link_in_setitem = True

            result.actual_mappings.setdefault(feature_name, set()).add((self.myid,expression)) # FIXME: 区分self和result

        # 删除self中存在但config中没有定义的列
        config_columns = set(config['feature'].dropna())
        original_columns = set(self.columns)
        columns_to_drop = original_columns - config_columns

        # inplace以避免生成新的MyDataFrame实例
        result._original_drop(columns=columns_to_drop, errors='ignore', inplace=True)

        # FIXME: 会造成追溯丢失，暂时去掉
        # result = _sort_columns(result)

        # 建立连接关系
        self.output_df = result
        result.input_dfs = [self]

        return result


    # 向前追踪指定df的指定列的计算逻辑
    # @Deprecated 此方法已被generate_dataflow()替代，后者输出更易读的图形化结果
    # def trace_column(self, feature_to_trace:str):
    #     assert isinstance(feature_to_trace, str)
    #
    #     # start_line: 倒序处理的开始行号（若为None则处理所有行）
    #     def _build_pipe_tree_recursive(df, feature, depth=0, start_line:int=None):
    #         if df.input_dfs is None:
    #             return None
    #
    #         if start_line is None:
    #             start_line  = len(df.actual_mappings)
    #
    #         # 倒序遍历
    #         # 获取 actual_mappings 的键值对列表
    #         mappings_list = list(df.actual_mappings.items())
    #         for idx in range(start_line - 1, -1, -1):  # 从 start_line-1 到 0
    #             mapped_feature, expr = mappings_list[idx]
    #             if mapped_feature == feature :
    #                 # 避免无限递归（同一个配置文件内部递归查找时）
    #                 # if df is self and feature == expr:
    #                 #     continue
    #                 input_names = _extract_column_names(expr)
    #
    #                 children = []
    #                 for name in input_names:
    #
    #                     # 同一个配置文件内部的递归匹配
    #                     # 从当前行的上一行继续倒序匹配
    #                     if idx > 1: # FIXME： 改为>0?
    #                         child_ast_self = _build_pipe_tree_recursive(df, name, depth + 1, idx -1)
    #                         if child_ast_self:
    #                             children.append(child_ast_self)
    #
    #                     # 前一个配置文件内的递归匹配
    #                     for input_df in df.input_dfs:
    #                         child_ast_prev = _build_pipe_tree_recursive(input_df, name, depth + 1)
    #                         if child_ast_prev:
    #                             children.append(child_ast_prev)
    #
    #                 return {
    #                     "feature": feature,
    #                     "df": df.copy(),
    #                     "mapping": {"feature": mapped_feature, "expression": expr},
    #                     "expression": expr,
    #                     "children": children,
    #                     "depth": depth
    #                 }
    #
    #     def _print_pipe_tree(ast_node, indent=0):
    #         if ast_node is None:
    #             print("└── (empty)")
    #             return
    #         spaces = "  " * indent
    #         expr = ast_node["expression"]
    #         feature = ast_node['feature']
    #         df = ast_node["df"]
    #         print(f"{spaces}└── [{df.attrs['name']}] {feature} = {expr} ")
    #         for child in ast_node["children"]:
    #             _print_pipe_tree(child, indent + 1)
    #
    #     tree = _build_pipe_tree_recursive(self, feature_to_trace)
    #     _print_pipe_tree(tree)
    #     return tree
    #
    #
    # # 向前追溯多个列
    # # @Deprecated 此方法已被generate_dataflow()替代，后者输出更易读的图形化结果
    # def trace_columns(self, features_to_trace:list):
    #     for feature in features_to_trace:
    #         print(feature)
    #         self.trace_column(feature)
    #         print()


    # 宽表转长表，例如：
    # k_ts, f1_mean_3D, f1_slope_3D, f2_mean_3D, f2_slope_3D
    # 2025 - 01 - 01, 1, 2, 3, 4
    # 2025 - 01 - 02, 5, 6, 7, 8
    # 转为：
    # k_ts, feature, measure, period, value
    # 2025 - 01 - 01, f1, mean, 3D, 1
    # 2025 - 01 - 01, f1, slope, 3D, 2
    # 2025 - 01 - 01, f2, mean, 3D, 3
    # 2025 - 01 - 01, f2, slope, 3D, 4
    # 2025 - 01 - 02, f1, mean, 3D, 5
    # 2025 - 01 - 02, f1, slope, 3D, 6
    # 2025 - 01 - 02, f2, mean, 3D, 7
    # 2025 - 01 - 02, f2, slope, 3D, 8
    def wide_to_long(self) -> MyDataFrame:
        id_vars = ['k_ts','k_device']
        value_vars = [col for col in self.columns if col != 'k_ts' and col != 'k_device']
        df_melted = self.melt(id_vars=id_vars, value_vars=value_vars, var_name='feature_measure_period',
                            value_name='value')
        split_cols = df_melted['feature_measure_period'].str.rsplit('_', n=2, expand=True)
        df_melted[['feature', 'measure', 'period']] = split_cols
        result = df_melted[['k_ts', 'k_device', 'feature', 'measure', 'period', 'value']]
        result = result.sort_values(['k_ts', 'feature', 'measure']).reset_index(drop=True)
        return MyDataFrame(result, myid=str(uuid.uuid4()))


    # 长表转宽表
    def long_to_wide(self) -> MyDataFrame:
        required_cols = ['k_ts', 'k_device', 'feature', 'measure', 'period', 'value']
        missing_cols = [col for col in required_cols if col not in self.columns]
        if missing_cols:
            raise ValueError(f"缺少必需的列: {missing_cols}")
        wide_df = self.copy()
        wide_df['new_col'] = wide_df['feature'] + '_' + wide_df['measure'] + '_' + wide_df['period']
        wide_df = MyDataFrame(wide_df.pivot(index=['k_ts', 'k_device'], columns='new_col', values='value'), myid=str(uuid.uuid4()))
        wide_df = wide_df.reset_index()
        wide_df.columns.name = None
        return wide_df


    # 生成数据流图
    # show_value: 是否显示此列数据值（第一行）
    # highlight_useless_column：是否高亮显示无输出edge的列（无用列）
    def generate_dataflow(self, filename: Union[str, Path] = None, show_value=False, highlight_useless_column=True):
        # graphviz需要本地安装应用（仅pip install graphviz不够），比较麻烦
        # 所以开发者可能本地没有生成数据流图的条件
        # 此时仅警告不实际生成图（不抛出异常以免影响测试用例的完成）
        try:
            import os
            import graphviz
            from graphviz import ExecutableNotFound
        except ImportError as e:
            print(f"警告: 未安装graphviz，请先安装graphviz应用，然后 pip install graphviz  {e}")
            return None

        if filename is not None:
            filename = Path(filename)
        if filename.suffix.lower() != '.svg':
            raise ValueError(f"仅支持 .svg 格式: {filename.suffix}")

        dot = graphviz.Digraph(comment='DataFlow Graph', format='svg')
        # ranksep: df矩形之间的横向距离（英寸）
        # nodesep: 列矩形之间的纵向距离（英寸）
        dot.attr(rankdir='LR', splines='spline', ranksep='1', nodesep='0.12', compound='true')
        # 设置中文字体，优先使用系统中存在的字体
        dot.attr('graph', fontname='SimHei,SimSun,Microsoft YaHei,DejaVu Sans,Arial,sans-serif', fontsize='12')
        dot.attr('node', fontname='SimHei,SimSun,Microsoft YaHei,DejaVu Sans,Arial,sans-serif',
                 shape='box', style='filled', fillcolor='white', fontsize='10', height='0.3')
        dot.attr('edge', fontname='SimHei,SimSun,Microsoft YaHei,DejaVu Sans,Arial,sans-serif')

        # 使用集合记录已访问的节点，避免重复处理
        visited_dfs = set()
        visited_edges = set()
        all_col_nodes = set()  # 记录所有列节点ID
        output_sources = set()  # 记录有出边的源节点ID

        def add_dataframe_node(df):
            """添加DataFrame节点到图中"""
            if df.myid in visited_dfs:
                return
            visited_dfs.add(df.myid)

            # 创建子图表示DataFrame，使用cluster前缀使graphviz将其渲染为带边框的组
            with dot.subgraph(name=f'cluster_{df.myid}') as c:
                # cluster的显示名称
                label = df.attrs["name"]
                if "op" in df.attrs:
                    label = f'{label}\\n({df.attrs["op"]})'
                label = "\\n".join(textwrap.wrap(label, width=20)) # 长文本加换行
                c.attr(label=label,
                       fontname='SimHei,SimSun,Microsoft YaHei,DejaVu Sans,Arial,sans-serif')
                c.attr(style='filled', color='lightgrey')
                c.attr(rankdir='TB')

                # 添加column矩形 - 强制垂直排列在同一列
                columns = _all_columns(df)  # FIXME：索引与普通列分别循环渲染更方便
                for i, col in enumerate(columns):
                    col_node_id = f'col_{df.myid}_{col}'

                    # 获取value（考虑col是普通列和索引两种情况）
                    value = None
                    if not df.empty:
                        if col in df.index.names:
                            # 对于多重索引，获取对应层级的值
                            if df.index.nlevels > 1:
                                # 获取第一个索引级别的位置
                                level_idx = df.index.names.index(col)
                                value = df.index[0][level_idx]
                            else:
                                # 单一索引情况
                                value = df.index[0]
                        elif col in df.columns:
                            # 普通列的情况
                            value = df.iloc[0][col]
                    else:
                        value = 'None'

                    label = f'{col} ({value})' if show_value else col
                    if col not in df.get_cols:
                        label = f'{col}*'
                    c.node(col_node_id, label=label)
                    all_col_nodes.add(col_node_id)

                # 强制垂直排列：避免同一df里两个列出现左右排列的情况，导致连线难以看清
                if len(columns) > 1:
                    with c.subgraph() as s:
                        s.attr(rank='same')
                        for i, col in enumerate(columns):
                            col_node_id = f'col_{df.myid}_{col}'
                            s.node(col_node_id)

        def build_graph_recursive(current_df):
            """递归构建图"""
            # 添加当前DataFrame节点
            add_dataframe_node(current_df)

            # 处理上游节点
            input_df_ids = set()
            for feature, sources in current_df.actual_mappings.items():
                for df_exp_pair in sources:  # sources 是 (df_id, expression) 元组集合
                    input_df_id = df_exp_pair[0]  # 第一个元素是 DataFrame ID
                    input_df_ids.add(input_df_id)
            for input_df_id in input_df_ids:
                if current_df.myid == input_df_id:
                    continue
                build_graph_recursive(_dataframes[input_df_id])

            # TODO: 根据mappings已经可以获取到inputs，未来可移除input_df的维护
            # for input_df in current_df.input_dfs:
            #     build_graph_recursive(input_df)

            # 根据actual_mappings创建列之间的连接
            # 注意：current_df内部不会有同名列；input_dfs之间不会有同名列(已不再，merge允许同名列了)；但current_df与input_dfs之间可能有同名列
            for feature, sources in current_df.actual_mappings.items():
                for df_exp_pair in sources:
                    input_df = _dataframes[df_exp_pair[0]]
                    create_edges_from_mapping(feature, df_exp_pair[1], input_df, current_df)

            # # 处理本节点内部连接
            # for feature, source in current_df.actual_mappings.items():
            #     # TODO：精简代码
            #     if isinstance(source, set):
            #         for df_exp_pair in source:
            #             create_edges_from_mapping(feature, df_exp_pair[0], df_exp_pair[1], current_df)
            #     else:
            #         create_edges_from_mapping(feature, source, current_df, current_df)

        # 根据feature mapping信息创建连接线
        def create_edges_from_mapping(feature, expression, input_df, current_df):
            target_feature = feature

            # 提取表达式中的输入列
            input_cols = _extract_column_names(expression)

            # 在上游DataFrame中找到对应的列并创建连接
            for input_col in input_cols:
                # 避免current_df列自身的连接
                if current_df is input_df and target_feature == input_col:
                    continue
                if input_col in _all_columns(input_df):
                    # 一些操作不会对df的列集合有影响，这种情况简化连线，
                    # 改为创建cluster间的连接，而非col之间的连接，以减少图中的连线数量
                    row_ops = ['concat', 'query', 'dropna']
                    if "op" in current_df.attrs and current_df.attrs['op'] in row_ops:
                        cluster_edge_key = (input_df.myid, current_df.myid)
                        if cluster_edge_key not in visited_edges:
                            input_cols_list = list(_all_columns(input_df))
                            output_cols_list = list(_all_columns(current_df))
                            if input_cols_list and output_cols_list:
                                representative_input = f'col_{input_df.myid}_{input_cols_list[0]}'
                                representative_output = f'col_{current_df.myid}_{output_cols_list[0]}'
                                # 参数ltail和lhead要求compound=true才有效
                                dot.edge(
                                    representative_input,
                                    representative_output,
                                    ltail=f'cluster_{input_df.myid}',
                                    lhead=f'cluster_{current_df.myid}'
                                )

                            visited_edges.add(cluster_edge_key)
                            for col_idx, col in enumerate(_all_columns(input_df)):
                                source_node_id = f'col_{input_df.myid}_{col}'
                                output_sources.add(source_node_id)
                    else:
                        target_node_id = f'col_{current_df.myid}_{target_feature}'
                        source_node_id = f'col_{input_df.myid}_{input_col}'

                        # 创建连接，避免重复边
                        edge_key = (source_node_id, target_node_id)
                        if edge_key not in visited_edges:
                            if input_df is current_df:
                                dot.edge(source_node_id, target_node_id, color='gray') # 同一个DataFrame内部的连接用灰色
                            else:
                                if input_col == target_feature:
                                    dot.edge(source_node_id, target_node_id, color='gray') # 同名列传递
                                else:
                                    dot.edge(source_node_id, target_node_id)
                            visited_edges.add(edge_key)
                            output_sources.add(source_node_id)


        # 从当前DataFrame开始构建图
        build_graph_recursive(self)

        # 如果启用了 highlight_useless_column，则将没有输出边的列高亮
        if highlight_useless_column:
            no_output_nodes = all_col_nodes - output_sources
            for node_id in no_output_nodes:
                dot.node(node_id, fillcolor='yellow')

        try:
            # 渲染图片，render里的filename参数不要带扩展名
            dot.render(os.path.splitext(filename)[0], cleanup=True)  # cleanup=True删除临时文件
            print(f"数据流图已保存到: {filename}")
            return dot
        except ExecutableNotFound as e:
            print(f"警告: 未安装graphviz应用，请先下载安装。 {e}")
            return None


    # 确保DataFrame的时间戳和设备列的类型，时间戳作为索引
    # 将object类型的列转为string类型，前者不支持eval()
    def format_columns(self) -> MyDataFrame:
        result = MyDataFrame(self)
        # result = self
        result.attrs['name'] = self.attrs['name']

        global _link_in_getitem
        _link_in_getitem = False
        if 'k_ts' in result.columns:
            result['k_ts'] = pd.to_datetime(result['k_ts'])
            # 若k_ts同时作为索引和普通列，对merge操作会报错（'k_ts' is both an index level and a column label, which is ambiguous.）
            # 若k_ts仅作为索引，df['k_ts']会报错 （KeyError)
            # result = result.set_index(['k_ts'], drop=True)
        if 'k_device' in result.columns:
            result['k_device'] = result['k_device'].astype(str)

        # 将object类型的列转为string类型，避免eval()里报错
        object_cols = result.select_dtypes(include=['object']).columns
        result[object_cols] = result[object_cols].astype('string')

        _link_in_getitem = True

        # 列名去掉首尾空格，防止难以察觉的错误
        result.columns = result.columns.str.strip()

        # 列名排序，方便调试对比
        # result = _sort_columns(result)

        return result


# 检验列名是否合法
def _validate_var_name(var_name: str):
    forbidden_chars = {'.', '[', ']', '-', '+', '*', '/', '\\', '%', '&'}
    if any(char in forbidden_chars for char in var_name):
        raise ValueError(f"变量名 '{var_name}' 包含非法字符")


# 先使用numexpr解析，若失败再尝试python解析
def _eval(df: MyDataFrame, expression: str) -> Series:
    result = None

    # dataframe的eval()方法不支持where表达式，自己实现
    if expression.startswith('where'):
        args = _parse_where_args(expression)
        if len(args) == 3:
            return np.where(_eval(df, args[0]), _eval(df, args[1]), _eval(df, args[2]))
        else:
            raise ValueError(f"无效的where表达式格式: {expression}")

    try:
        result = df.eval(expression, engine='numexpr')
    except Exception as e:
        # numexpr不支持字符串等操作，此时尝试降级到python解释器（性能较低）
        # 典型错误信息：'unknown type object'、'unknown type datetimedelta64[ns]'
        try:
            result = df.eval(expression, engine='python')
        except Exception as e:
            # 如果python解析器也失败，报错
            cols = _extract_column_names(expression)
            print(f'\n表达式执行失败：{expression}，失败原因：{e}')
            print(f'输入数据相关列：')
            print(df[cols])
            raise Exception(f'表达式 {expression} 执行失败(python)： {e}')
    return result


# 为解决嵌套where()的情况，将原来的正则表达式方案改为手动解析方案
def _parse_where_args(s):
    if not s.startswith('where(') or not s.endswith(')'):
        raise ValueError("Not a where expression")
    # 去掉 'where(' 和最后的 ')'
    inner = s[6:-1]
    args = []
    paren_level = 0
    current = []
    for char in inner:
        if char == ',' and paren_level == 0:
            args.append(''.join(current).strip())
            current = []
        else:
            if char == '(':
                paren_level += 1
            elif char == ')':
                paren_level -= 1
            current.append(char)
    args.append(''.join(current).strip())  # 最后一个参数
    return args


def _extract_column_names(expr: str):
    if expr.startswith('where'):
        args = _parse_where_args(expr)
        # FIXME: 根据实际情况，选择arg[1]或arg[2]
        return [] # FIXME

    # FIXME：带有@pd的表达式无法解析（如 @pd.shape[0]) ）
    if '@' in expr:
        return [] # FIXME

    tree = ast.parse(expr, mode='eval')
    names = set()

    class NameVisitor(ast.NodeVisitor):
        def visit_Name(self, node):
            names.add(node.id)
            self.generic_visit(node)

    NameVisitor().visit(tree)
    return sorted(names)  # 或直接返回 names（set）


# 列按字母顺序排序
def _sort_columns(df: pd.DataFrame):
    cols = sorted(df.columns)
    if 'k_device' in cols:
        cols = ['k_device'] + [col for col in cols if col != 'k_device']
    if 'k_ts' in cols:
        cols = ['k_ts'] + [col for col in cols if col != 'k_ts']
    # 不使用df[cols]的写法，避免产生追溯记录
    return df.reindex(columns=cols)


# 当df仅有默认索引时，直接返回不包含索引的列
# 若df有k_ts等命名索引时，返回包含这些索引的所有列
def _all_columns(df: pd.DataFrame):
    if any(name is not None for name in df.index.names):
        index_names = set(df.index.names)
        column_names = set(df.columns)
        intersection = index_names & column_names
        # 如果普通列与索引存在同名项，先移除这些列再reset_index以避免冲突
        if intersection:
            df_for_iter = df.drop(columns=list(intersection))
            df_for_iter = df_for_iter.reset_index()
        else:
            df_for_iter = df.reset_index()
    else:
        df_for_iter = df
    return df_for_iter.columns


# K2Pipe提供的内置函数，用于解决暂时无法通过eval()实现的常用操作，如时间操作
def time_shift(self: Series, *args, **kwargs):
    return self + pd.to_timedelta(*args, **kwargs)


# 修改pd.concat()方法
# 注意：merge和join也会调用自定义concat()方法
_original_concat = pd.concat
def my_concat(objs, axis=0, **kwargs):
    result = _original_concat(objs, axis=axis, **kwargs)

    for i, obj in enumerate(objs):
        if not isinstance(obj, MyDataFrame) and isinstance(obj, pd.DataFrame):
            objs[i] = MyDataFrame(obj, myid=str(uuid.uuid4()))

    if not isinstance(result, MyDataFrame) and isinstance(result, pd.DataFrame):
        result = MyDataFrame(result, myid=str(uuid.uuid4()))

    if axis == 0:
        # 纵向拼接的情况（不会有Series情况）
        assert isinstance(result, pd.DataFrame)
        result.attrs['op'] = 'concat'
        # 建立连接关系
        for obj in objs:
            result.input_dfs.append(obj)
            for col in obj.columns:
                obj.get_cols.add(col)
                result.actual_mappings.setdefault(col, set()).add((obj.myid,col))
    elif axis == 1:
        # 横向拼接的情况（可能有Series情况）
        assert isinstance(result, pd.DataFrame) or isinstance(result, pd.Series)

        result.attrs['op'] = 'concat/1'

        all_features = []

        # 验证是否符合横向拼接的条件
        for obj in objs:
            if isinstance(obj, pd.Series):
                all_features.append(obj.name)
            elif isinstance(obj, pd.DataFrame):
                # merge的实现会调用concat(axis=1)
                # 虽然pandas的concat支持两个df有同名列，但结果格式复杂嵌套容易出错，这里禁止这种情况
                if bool(set(all_features) & set(obj.columns.values)):
                    raise ValueError(f'横向拼接的DataFrame不能有同名列：{all_features}  -- {obj.columns.values}')
                all_features.extend(obj.columns)
            else:
                raise ValueError('暂不支持非DataFrame、Series类型的拼接')

        # 建立连接关系
        for obj in objs:
            if isinstance(obj, pd.Series):
                df = MyDataFrame(obj, myid=str(uuid.uuid4()))
                df.attrs['name'] = 'Series'
                result.input_dfs.append(df)
                result.actual_mappings.setdefault(obj.name, set()).add((df.myid, obj.name))
                df.get_cols.add(obj.name)
            elif isinstance(obj, MyDataFrame):
                result.input_dfs.append(obj)
                obj.output_df = result
                for col in obj.columns:
                    result.actual_mappings.setdefault(col, set()).add((obj.myid, col))
                    obj.get_cols.add(col)
            else:
                raise ValueError('暂不支持非DataFrame、Series类型的拼接')
    else:
        raise ValueError('axis参数只能为0或1')

    return result


# 替换 pandas 的 read_csv
_original_read_csv = pd.read_csv
def my_read_csv(filepath_or_buffer, *args, **kwargs):
    df = _original_read_csv(filepath_or_buffer, *args, **kwargs)
    if isinstance(filepath_or_buffer, (str, Path)):
        filename = Path(filepath_or_buffer).name
        df = MyDataFrame(df)
        df.attrs['name'] = filename
    return df