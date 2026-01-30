# 这是一个matplotlib显示中文的库，只要你在文件开头调用即可
# 调用方式
# from yxspkg import matplotlib_chinese

from pathlib import Path 
import sys
import os
import json
import shutil
from urllib import request
from matplotlib import font_manager
import matplotlib as mpl

mpl.rcParams['font.family'] =['Times New Roman','SimSun']
