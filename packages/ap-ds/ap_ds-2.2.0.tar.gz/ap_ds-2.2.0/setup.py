
from setuptools import setup, find_packages
import os

# 读取README.md
def read_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "DVS Audio Library - Advanced audio processing and playback"

# 获取README内容（包含README.md和Correct-Suggestions-Guide.md）
long_description = read_file("README.md")
guide_content = read_file("Correct-Suggestions-Guide.md")
if guide_content and not guide_content.startswith("DVS Audio"):
    long_description += "\n\n" + guide_content

setup(
    name="ap-ds",
    version="2.2.0",  # 更新版本号
    description="DVS Audio Library - Advanced audio processing and playback",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DVS",
    author_email="me@dvsyun.top",
    url="https://www.dvsyun.top/ap_ds",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        # 修改许可为自定义许可
        "License :: Other/Proprietary License",  # 自定义许可
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="audio music playback sdl2",
    python_requires=">=3.7",
    install_requires=[],  # 纯Python依赖
    include_package_data=True,
    # 添加许可证信息
    license="DVS Audio Library © （ap_ds ©） - All rights reserved",
    # 确保包含所有必要的文件
    package_data={
        '': ['*.md', '*.txt'],  # 包含所有markdown和文本文件
    },
)
