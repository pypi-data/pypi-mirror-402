from sympy import sympify, lambdify, Symbol, Number
from sympy.core.numbers import NaN as spnan
from sympy.core.relational import Relational
from sympy.core.numbers import Float, Integer
from sympy.logic.boolalg import Boolean
from pandas import DataFrame
import pandas as pd
from typing import Union
import numpy as np
from ks_utility.object import BaseException

BASIC_TYPES = [int, float, str, Float, Integer, spnan]

def is_basic_type(a):  
    for basic_type in BASIC_TYPES:
        if isinstance(a, basic_type):
            return True
    return False

def convert(x):
    if isinstance(x, Number):
        val = float(x)
        return int(val) if val == int(val) else val
    return x

class MathsException(BaseException):
    pass

class ExpressionCache:
    """用于缓存表达式和对应矢量化函数的类"""
    _cache = {}

    @classmethod
    def get_calculator(cls, expression, safe_keys = []):
        """获取或创建表达式的矢量化计算器"""
        if expression not in cls._cache:
            cls._cache[expression] = VectorizedExpressionCalculator(expression, safe_keys)
        return cls._cache[expression]

# row方法
# 支持 判断a字段在b字段的数组中(b字段是一个数组)
def isin_row(a, b):
    return [ai in bi for ai, bi in zip(a, b)]

def nanmean(*args):
    # args 是若干个 pandas Series（列）
    return np.array([np.nanmean(row) for row in zip(*args)])

def nansum(*args):
    # args 是若干个 pandas Series（列）
    return np.array([np.nansum(row) for row in zip(*args)])

def nanmax(*args):
    # args 是若干个 pandas Series（列）
    return np.array([np.nanmax(row) for row in zip(*args)])

def nanmin(*args):
    # args 是若干个 pandas Series（列）
    return np.array([np.nanmin(row) for row in zip(*args)])

# a 是pandas Series，里边每个元素是一个数组
def ema(a, n: int):
    # args 是若干个 pandas Series（列）
    v = a.transform(lambda x: pd.Series(x).ewm(span=n, adjust=False).mean().iloc[-1])
    return v

def log(a):
    return a.transform(lambda x: np.log(x))

def log10(a):
    return a.transform(lambda x: np.log10(x))

## col 方法
def rollingmeancol(a, window: int, min_periods: int = None):
    # args 是若干个 pandas Series（列）
    return a.rolling(window, min_periods=min_periods).mean()

def nanmeancol(a):
    # args 是若干个 pandas Series（列）
    return a.mean(skipna=True).repeat(len(a))

def nansumcol(a):
    # args 是若干个 pandas Series（列）
    return a.sum(skipna=True).repeat(len(a))

def nanmaxcol(a):
    # args 是若干个 pandas Series（列）
    return a.max(skipna=True).repeat(len(a))

def nanmincol(a):
    # args 是若干个 pandas Series（列）
    return a.min(skipna=True).repeat(len(a))

# 支持 shift函数
def shift(a, b: int = 1):
    # args 是若干个 pandas Series（列）
    return a.shift(b)

class VectorizedExpressionCalculator:
    """矢量化表达式计算类"""
    def __init__(self, expression, safe_keys = []):
        # 将表达式字符串转换为 SymPy 表达式
        self.variables = []
        self.expression = sympify(expression, locals={k: Symbol(k) for k in safe_keys}, evaluate=False)
        # 将 SymPy 表达式转换为矢量化函数（支持 NumPy/Pandas 运算）
        
        if isinstance(self.expression, list):
            # 每个元素单独构建一个子表达式计算器
            self.sub_calculators = [
                VectorizedExpressionCalculator(str(f'"{sub_exp}"' if type(sub_exp) == str else str(sub_exp)), safe_keys)
                for sub_exp in self.expression
            ]
            self.calculate_dataframe = lambda df: [
                [
                    sub_cal.calculate_dataframe(df).loc[i] 
                    for sub_cal in self.sub_calculators
                ]
                for i in df.index
            ]
            return
            
        
        # 如果是传入基本的数据类型，例如数组之类的，直接返回
        if is_basic_type(self.expression):
            # 直接返回len(df) * x 个值
            self.calculate_dataframe = lambda df: pd.Series([self.expression] * len(df), index=df.index)
            return
            
        self.variables = sorted(self.expression.free_symbols, key=lambda x: str(x)) # 这里要用sorted很关键，因为set是没有顺序的，会导致值计算错误
        self.vectorized_func = lambdify(
            self.variables,
            self.expression,
            modules=[{
                'max': np.maximum,
                'min': np.minimum,
                '&': np.logical_and,
                '|': np.logical_or,
                '==': np.equal,
                '>': np.greater,
                '<': np.less,
                '>=': np.greater_equal,
                '<=': np.less_equal,
                'isin': isin_row,  # 覆盖原本的 np.isin
                'nansum': nansum,
                'nanmean': nanmean,
                'nanmax': nanmax,
                'nanmin': nanmin,
                'nansumcol': nansumcol,
                'rollingmeancol': rollingmeancol,
                'nanmeancol': nanmeancol,
                'nanmaxcol': nanmaxcol,
                'nanmincol': nanmincol,
                'nan': np.nan,
                'shift': shift,
                'ema': ema,
                'log': log,
                'log10': log10
            }, 'numpy']
        )

    def calculate_dataframe(self, df):
        # 确保 DataFrame 中包含表达式需要的所有变量
        required_columns = [str(x) for x in self.variables]
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # 新增：将布尔列转为整数
        inputs = []
        for col in required_columns:
            s = df[col]
            if s.dtype == bool:
                s = s.astype(int)
            inputs.append(s)
        
        # 使用矢量化函数计算
        return self.vectorized_func(*inputs)


def calculate_expression(expression, df):
    """接口函数，直接传入表达式和 DataFrame 进行计算"""
    calculator = ExpressionCache.get_calculator(expression)
    return calculator.calculate_dataframe(df)

def cal_exp(exp: str, values: Union[dict, DataFrame], safe_keys: list[str]=[]):
    try:
        single_run = isinstance(values, dict)
        if single_run:
            values = pd.DataFrame([values])
        calculator = ExpressionCache.get_calculator(exp, safe_keys)
        series = pd.Series(calculator.calculate_dataframe(values))
        series = series.apply(convert)
        series.index = values.index # 保持原有的索引,如果是按照group传入，index是会被打乱的，我们需要保持传入的索引
        return series if not single_run else (series.iloc[0] if len(series) else None)
    except Exception as e:
        raise MathsException(f"表达式{exp}计算错误：{str(e)}", data={'values': values})

# t = cal_exp('a+b+c', pd.DataFrame({'a': [1,2,3], 'b': [2,3,4], 'c': [3,4,5]}))
# t = cal_exp('where(a>=2, where(b>=4, b, 999), c)', pd.DataFrame({'a': [1,2,3], 'b': [2,3,4], 'c': [3,4,5]}))
# t = cal_exp('[nan,2.2,a*2,b*2,c*3]', pd.DataFrame({'a': [1,2,3], 'b': [2,3,4], 'c': [3,4,5]}))
# t = cal_exp('[6,2,a*2,b*2]', pd.DataFrame({'a': [1,2,3], 'b': [2,3,4], 'c': [3,4,5]}))
# t = cal_exp('["a", " ", a, ""]', pd.DataFrame({'a': [1,2,3], 'b': [2,3,4], 'c': [3,4,5]}))
# t = cal_exp("['a', ' ', a, '']", pd.DataFrame({'a': [1,2,3], 'b': [2,3,4], 'c': [3,4,5]}))
# t = cal_exp("shift(a, 2)", pd.DataFrame({'a': [1,2,3], 'b': [-2,3,4], 'c': [3,4,5]}))
# t = cal_exp("nanmaxcol(a)", pd.DataFrame({'a': [1,2,3], 'b': [-2,3,4], 'c': [3,4,5]}))
# t = cal_exp("nansumcol(a)", pd.DataFrame({'a': [1,2,np.nan], 'b': [-2,3,4], 'c': [3,4,5]}))
# t = cal_exp("nanmeancol(a)", pd.DataFrame({'a': [1,2,np.nan], 'b': [-2,3,4], 'c': [3,4,5]}))
# t = cal_exp("nanmaxcol(a)", pd.DataFrame({'a': [1,2,np.nan], 'b': [-2,3,4], 'c': [3,4,5]}))
# t = cal_exp("nanmincol(a)", pd.DataFrame({'a': [1,2,np.nan], 'b': [-2,3,4], 'c': [3,4,5]}))
# t = cal_exp("nanmaxcol(shift(a,2))", pd.DataFrame({'a': [4,3,2,np.nan], 'b': [1,-2,3,4], 'c': [1,3,4,5]}))
# if __name__ == "__main__":
#     t = cal_exp("ema(log(a),5)", pd.DataFrame({'a': [[76.5,74.81,79.19,79.3,76.09],[1,2,3,4,5],[1,2,3,4,5],np.nan], 'b': [1,-2,3,4], 'c': [1,3,4,5]}))
#     print(t)