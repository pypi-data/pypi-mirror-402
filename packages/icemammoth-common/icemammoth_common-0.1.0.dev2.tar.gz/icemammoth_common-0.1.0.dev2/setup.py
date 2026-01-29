import os
from setuptools import setup, find_packages



# 读取依赖文件
current_dir = os.path.dirname(os.path.abspath(__file__))
requirements_path = os.path.join(current_dir, "requirements.txt")
readme_path = os.path.join(current_dir, "README.md")
with open(requirements_path, "r", encoding="utf-8") as f:
    install_requires = f.read().splitlines()

setup(
    name='icemammoth_common',
    version='0.1.0.dev.1',
    # find_packages()会自动发现项目中的所有包和子包。
    # 默认情况下，find_packages() 会递归地查找所有包含 __init__.py 的目录，并将它们视为包。where表示从哪个目录开始搜索
    packages=find_packages(where=".",include=["icemammoth_common","icemammoth_common.*"], exclude=["test", "test.*"]),
    # 指定包的源代码位置, 控制包的安装路径: package_dir = {"<目标路径>": "<源代码路径>"}
    # 目标路径：表示包在安装后应该被放置的目录结构。通常是一个空字符串 ""，表示项目的根目录。
    # 源代码路径：表示包的源代码实际存放的位置。
    # 一般不需要设置，因为默认情况下，Python 会自动将包名作为模块名，并使用点号（.）分隔。
    # package_dir={"icemammoth_common": "icemammoth_common"},          
    description='common tools collection',
    long_description=open(readme_path).read(),
    long_description_content_type='text/markdown',
    author='Klein',
    author_email='myicemammoth@gmail.com',
    url='',
    # 许可证类型
    license='MIT', 
    classifiers=[
        # 包分类列表，例如：
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.12',
    ],
    keywords='common utils',
    install_requires= install_requires, # 依赖项（从 requirements.txt 读取）
    # 如果你的模块包含数据文件，可以在这里添加 package_data 字段
    # package_data={
    #     'common': ['data/*.dat'],
    # },
    # 如果你的模块包含二进制文件，可以在这里添加 ext_modules 字段
    # ext_modules=[
    #     # 你的扩展模块
    # ],
    # 测试配置（可选）
    # test_suite="test",  # 指定测试模块
    # tests_require=["pytest"],  # 测试依赖
)