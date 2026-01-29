# norfetools/__init__.py
from typing import Optional

from .Bibcleaner import Bib
from .FileTools import Sl


# === 引入工具函数 ===
from .norfetools import (
    Set_colorbar_ticks_inward,
    Set_colorbar_ticks_outward,
    Set_axis_formatting,
    SetColor,
    TestColorList,
    Save_Fig,
    SaveFig,
    Set_style,
    Save_data,
    Load_data,
    SaveData,
    LoadData,
    Ensure_directory_exists
)


from .colors import (
    ALL_CARDS as _ALL_CARDS,
    CLL as _CLL,
    get_cmap_by_index as _get_cmap_by_index,
    make_dark_light_dark as _make_dark_light_dark,
)

# ---- Public aliases (what users import as `nt`) ----
# 常用：行向量色卡矩阵
CCL = _CLL              # 你要求的名字：nt.CCL

# 生成单一卡 / 对撞卡的公开 API（名字按你的要求）
def get_cmap_one(
    idx: int,
    reverse: bool = False,
    name: Optional[str] = None,
    discrete: Optional[int] = None,
):
    """Wrapper to colors.get_cmap_by_index"""
    return _get_cmap_by_index(idx, reverse=reverse, name=name, discrete=discrete)

def get_cmap_two(
    id1: int,
    id2: int,
    name: Optional[str] = None,
    drop_duplicate: bool = True,
    discrete: Optional[int] = None,
):
    """Wrapper to colors.make_dark_light_dark"""
    return _make_dark_light_dark(
        id1, id2, name=name, drop_duplicate=drop_duplicate, discrete=discrete
    )


__all__ = ['Bib', 
            'Sl',
            "Set_colorbar_ticks_inward",
            "Set_colorbar_ticks_outward",
            "Set_axis_formatting",
            "SetColor",
            "TestColorList",
            "Save_Fig",
            "SaveFig",
            "Set_style",
            "Save_data",
            "Load_data",
            "SaveData",
            "LoadData",
            "Ensure_directory_exists",
            "CCL",
            "ALL_CARDS",
            "get_cmap_one",
            "get_cmap_two",
            ]



import matplotlib.pyplot as plt

import matplotlib as mpl

from contextlib import contextmanager
import warnings


try:
    # plt.style.use(["science", "grid"])
    plt.style.use(["science", ])
except OSError:
    warnings.warn(f"Matplotlib style load failed. Using default style.", UserWarning)


# 设置网格透明度为0.2
mpl.rcParams.update({
    'axes.grid': True,           # 启用主坐标轴网格线
    'grid.alpha': 0.4,           # 网格线透明度
    'grid.linestyle': ':',       # 网格线样式（点状）
    'grid.color': 'black'        # 网格线颜色
})

mpl.rcParams.update({
    'legend.frameon': True,           # 显示图例边框
    'legend.facecolor': 'white',      # 图例背景颜色
    'legend.edgecolor': '#cccccc',      # 图例边框颜色
    'legend.framealpha': 1.0,         # 图例背景不透明度（1为不透明，0为透明）
    'legend.fancybox': True          # 若为True则边框为圆角，False为直角
})

mpl.rcParams.update({
    'axes.labelsize': 8,        # x/y 轴标签字体大小
    'xtick.labelsize': 8,       # x轴刻度字体
    'ytick.labelsize': 8,       # y轴刻度字体
    'legend.fontsize': 8,       # 图例字体大小
    'axes.titlesize': 8         # 标题字体大小（若使用）
})


DPI_SAVE = 800 # 默认的DPI设置，用于保存图像
CM = 1 / 2.54  # 1 英寸 = 2.54 厘米


@contextmanager
def Set_style(styles = ["science", "nature", "grid"]):
    with plt.style.context(styles):
        yield
