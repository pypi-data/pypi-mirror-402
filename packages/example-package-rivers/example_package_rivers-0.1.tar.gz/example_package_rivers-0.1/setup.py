from setuptools import setup, find_packages

setup(
    name='example_package_rivers',
    version='0.1',
    packages=find_packages(),
    description='A simple example package',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='http://github.com/yourusername/my_package',
    author='Rivers',
    author_email='xuec_7@163.com',
    license='MIT',
    install_requires=[
        # 依赖列表
    ],
    classifiers=[
        # 分类信息
    ]
)
