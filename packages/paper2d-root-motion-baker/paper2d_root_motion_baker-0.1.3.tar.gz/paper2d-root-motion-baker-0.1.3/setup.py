from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="paper2d-root-motion-baker",
    version="0.1.3",
    author="ocarina",
    description="A Python tool for baking root motion data from PNG sequence frames into JSON format",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ocarina/paper2d-root-motion-baker",
    license="MIT",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "Pillow>=10.0.0",
        "numpy>=1.24.3",
        "PyYAML>=6.0.1",
    ],
    entry_points={
        "console_scripts": [
            "prmb=paper2d_root_motion_baker.cli:main",
        ],
    },
    package_data={
        "paper2d_root_motion_baker": ["config.yaml"],
    },
    include_package_data=True,
)
