import setuptools

"""
打包教程：https://packaging.python.org/en/latest/tutorials/packaging-projects/

setuptools.setup 参数说明
name	包名称
version	包版本
author	程序的作者
author_email	程序的作者的邮箱地址
maintainer	维护者
maintainer_email	维护者的邮箱地址
url	程序的官网地址
license	程序的授权信息
description	程序的简单描述
long_description	程序的详细描述
platforms	程序适用的软件平台列表
classifiers	程序的所属分类列表
keywords	程序的关键字列表
packages	需要处理的包目录(通常为包含 __init__.py 的文件夹)
py_modules	需要打包的 Python 单文件列表
download_url	程序的下载地址
cmdclass	添加自定义命令
package_data	指定包内需要包含的数据文件
include_package_data	自动包含包内所有受版本控制(cvs/svn/git)的数据文件
exclude_package_data	当 include_package_data 为 True 时该选项用于排除部分文件
data_files	打包时需要打包的数据文件，如图片，配置文件等
ext_modules	指定扩展模块
scripts	指定可执行脚本,安装时脚本会被安装到系统 PATH 路径下
package_dir	指定哪些目录下的文件被映射到哪个源码包
entry_points	动态发现服务和插件，下面详细讲
python_requires	指定运行时需要的Python版本
requires	指定依赖的其他包
provides	指定可以为哪些模块提供依赖
install_requires	安装时需要安装的依赖包
extras_require	当前包的高级/额外特性需要依赖的分发包
tests_require	在测试时需要使用的依赖包
setup_requires	指定运行 setup.py 文件本身所依赖的包
dependency_links	指定依赖包的下载地址
zip_safe	不压缩包，而是以目录的形式安装
"""

with open('README.md', 'r', encoding='utf-8') as fp:
    long_description = fp.read()
with open('src/easemysql/__init__.py', 'r', encoding='utf-8') as fp:
    for line in fp.readlines():
        if line.startswith('VERSION'):
            version = line.split('=')[1].strip().strip("'").strip('"')
            break

setuptools.setup(
    version=version,
    name="easemysql",
    author="jaifire",
    author_email="boydearea@163.com",
    description="简单易用的 mysql 封装",
    long_description_content_type="text/markdown",
    long_description=long_description,
    url="https://gitee.com/jaifire/easemysql",

    # 将名为 "easemysql" 的包纳入分发,
    packages=["easemysql"],

    # packages 将从 src 目录加载，而不是从项目根目录
    # 空字符串 "" 键表示根包
    package_dir={"": "src"},

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
    ],
    python_requires=">=3.6"
)

"""
本地安装：python setup.py install

pip install build
pip install --upgrade twine

python -m build
twine upload dist/*
"""
