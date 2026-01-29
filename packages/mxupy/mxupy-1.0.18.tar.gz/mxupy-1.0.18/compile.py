from setuptools import setup, find_packages
# 如果是在虚拟环境中，必须先激活对应的环境，再执行下面的命令，否则无效
# python compile.py develop
# 记得将 C:\ProgramData\miniconda3\envs\myBase\Lib\site-packages\pywin32_system32 拷贝到 windows/system32 下面
# 如果报错 ImportError: DLL load failed while importing win32clipboard: 找不到指定的程，则： conda uninstall pywin32  / conda install pywin32
# python compile.py bdist_wheel
setup(
    name='mxupy',
    version='1.0.5',
    description='An many/more extension/utils for python',
    author='jerry',
    author_email='6018421@qq.com',
    url='http://www.xtbeiyi.com/',
    packages=find_packages(),
)
