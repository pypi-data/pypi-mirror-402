from setuptools import setup, find_packages

setup(
    name="structocr",
    version="1.1.1",
    description="The official Python SDK for StructOCR API - Passport, ID card, Driver License OCR, and Invoice.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    
    author="StructOCR Team",
    author_email="support@structocr.com",
    
    # 1. 这里通常放主页或者 GitHub 地址 (PyPI 标题下的链接)
    url="https://structocr.com", 
    
    # 2. 这里定义侧边栏的具体链接 (Homepage, Documentation, Source 等)
    project_urls={
        "Homepage": "https://structocr.com",
        "Documentation": "https://www.structocr.com/developers", # 假设你的文档在这里
        "Source": "https://github.com/structocr/structocr-python",
        "Tracker": "https://github.com/structocr/structocr-python/issues", # 问题追踪
    },

    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Image Recognition",
    ],
    python_requires='>=3.6',
)