from setuptools import setup, find_packages

setup(
    name="emotitext",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],  # Əgər başqa kitabxanadan asılılıq varsa bura yazılır
    author="Sənin Adın",
    description="Mətnlərə avtomatik emojilər əlavə edən kitabxana",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/istifadəçi_adın/emotitext",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)