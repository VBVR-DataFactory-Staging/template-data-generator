from setuptools import find_packages, setup

setup(
    name="multi-view-data-generator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "Pillow>=10.0.0",
        "opencv-python>=4.8.0",
        "pydantic>=2.0.0",
    ],
    python_requires=">=3.8",
)
