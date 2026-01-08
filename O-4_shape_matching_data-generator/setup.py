from setuptools import setup, find_packages

setup(
    name="shape-matching-task-generator",
    version="0.1.0",
    description="Shape matching task data generator",
    author="VM Dataset Team",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.26.4",
        "Pillow>=10.4.0",
        "pydantic>=2.10.5",
        "opencv-python>=4.10.0.84",
    ],
    python_requires=">=3.8",
)
