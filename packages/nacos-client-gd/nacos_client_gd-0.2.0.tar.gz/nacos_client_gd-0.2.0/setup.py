# setup.py
from setuptools import setup, find_packages
import os

# 读取README.md作为长描述
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

# 读取版本号（也可以直接写，推荐从__init__.py读取）
def get_version():
    init_path = os.path.join("nacos_client", "__init__.py")
    with open(init_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.strip().split("=")[1].strip().strip('"')
    return "0.2.0"

setup(
    name="nacos-client-gd",  # 库名（必须唯一！PyPI上不能重名，建议加自定义后缀）
    version=get_version(),       # 版本号（遵循语义化：主版本.次版本.补丁，如0.1.0）
    author="baoqian",            # 作者
    author_email="baoqian188@163.com",  # 作者邮箱
    description="自定义的Nacos 3.1.0客户端库，支持配置查询/修改、服务实例查询",  # 简短描述
    long_description=long_description,  # 长描述（README内容）
    long_description_content_type="text/markdown",  # 长描述格式
    url="https://github.com/baoqian188_baoqian/nacos-client-custom",  # 项目地址（可选）
    packages=find_packages(),    # 自动查找所有包（即nacos_client/）
    classifiers=[                # 分类标签（PyPI展示用，可选）
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",     # 支持的Python版本
    install_requires=[           # 依赖（和requirements.txt一致）
        "requests>=2.31.0",
        "pyyaml>=6.0.1",
    ],
)