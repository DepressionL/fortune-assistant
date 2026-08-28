"""pytest 公共配置：把项目根目录加入 sys.path。"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
