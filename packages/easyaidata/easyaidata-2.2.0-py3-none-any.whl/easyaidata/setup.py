from setuptools import setup
import os

# 获取项目根目录
project_root = os.path.abspath(os.path.dirname(__file__))

# 定义需要包含的非Python文件
package_data = {
    'easyaidata': [
        'ico/*',
        'settings/*',
        'extensions/*',
        'core/*.pyd',
        'core/skills_plugins/*',
        '*.pyd',
        '*.py',  # 包含所有Python文件
        'core/*.py',
        'core/skills_plugins/*.py'
    ],
}

# 从app.py和core文件夹中提取所有依赖
install_requires = [
    'pandas',
    'numpy',
    'Pillow',
    'tksheet',
    'polars>=0.0.1',
    'pyarrow>=0.0.1',
    'requests',
    'python-docx',
    'pydantic',
    'matplotlib',
    # tkinter是Python标准库，不需要单独安装
    # os, sys, threading, sqlite3等都是标准库，不需要单独安装
]

setup(
    name='easyaidata',
    version='2.2.0',
    description='A easy-to-use data processing tool with GUI',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://example.com/easyaidata',
    packages=['easyaidata'],
    package_dir={'easyaidata': '.'},
    package_data=package_data,
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'easyaidata=easyaidata.load:main',
        ],
    },
    platforms=['Windows'],
    license='Proprietary Non-Commercial',
    data_files=[('', ['LICENSE.txt'])],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Operating System :: Microsoft :: Windows',
    ],
    python_requires='>=3.8',
)
