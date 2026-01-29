from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="loopwn",
    version="0.1.0",
    author="loophatch",  # 作者名
    author_email="loophatch@example.com",  # 建议修改为你的真实邮箱
    description="A CTF pwn helper library for easy libc address calculation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/loophatch/loopwn",  # 项目主页
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'pwntools',
    ],
)
