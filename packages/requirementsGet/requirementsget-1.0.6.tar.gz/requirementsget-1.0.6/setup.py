from setuptools import setup, find_packages

with open("./README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="requirementsGet",
    version="1.0.6",
    description="读取指定路径下项目所用所有库，生成一个requirements.txt",
    license="MIT License",
    install_requires=[],
    packages=find_packages(),
    include_package_data=True,  # 自动打包文件夹内所有数据
    author="Ysasm",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author_email="1613921123@qq.com",
    url="https://gitee.com/YSASM",
    # packages=setuptools.find_packages(),
    classifiers=["Programming Language :: Python :: 3"],
)
