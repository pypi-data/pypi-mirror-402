from time import time
import setuptools
# c:\Python38\python.exe setup.py clean --all
# c:\Python38\python.exe setup.py sdist
# c:\Python38\python.exe -m build
# c:\Python38\python.exe -m twine upload dist/* --skip-existing
# 用户名 jerry1979

# API tokens 会过一段时间消失，需要自己再去创建

# pypi-AgEIcHlwaS5vcmcCJGE5OWJhOTg1LWYzODAtNDUwZC1hNjhhLTlkZWZhYWFhMjg1ZQACKlszLCIzNWQzNjY4My0xMTllLTQ1MGItYjcxOC01ODEyNzM5YWRhYTAiXQAABiCwNAt78Brwwrqd90FC5vH78uhTyNllGrCzjuaVB-xtGw
# 
# 在HOME目录下建立 .pypirc 文件可以更为便捷的配置 token：
'''
[pypi]
  username = jerry1979
  password = pypi-AgEIcHlwaS5vcmcCJGM4NjY2NWQxLTA2MDgtNDcwZi04NjkxLTAzYzJmMTVhYWYxNQACKlszLCIzNWQzNjY4My0xMTllLTQ1MGItYjcxOC01ODEyNzM5YWRhYTAiXQAABiA0FKQQ6yClqIcEieFhsIzGeCBl6umg5WMojhuqPZo2Ig
'''
# PyPI recovery codes
'''
1eafff318d32b0a3
d4a7603081e9304f
9d000e851bd9efc4
2c2ce143c9c35850
5eb8f324aead0021
ca313984d96ce430
c7d120a4ba52fe21
c979515f991e420f
'''

# (myBase) E:\BaiduSyncdisk\pyLib\mxupyPackage>python setup.py sdist bdist_wheel

# with open("README.md", "r", encoding="utf-8") as fh:
#     long_description = fh.read()

# 要注意，每个包下面必须有__init__.py文件，find_packages需要

setuptools.setup(
    name="mxupy",
    version="1.0.18",
    author="jerry1979",
    author_email="6018421@qq.com",
    description="An many/more extension/utils for python",
    url="http://www.xtbeiyi.com/",
    packages=setuptools.find_packages(),
)
