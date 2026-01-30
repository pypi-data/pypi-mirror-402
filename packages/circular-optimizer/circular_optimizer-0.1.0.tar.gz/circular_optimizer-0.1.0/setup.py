from setuptools import setup, find_packages

setup(
    name="circular-optimizer",
    version="0.1.0",
    description="Gradient-based optimizer with circular exploration",
    author="isa",
    packages=find_packages(),
    install_requires=["torch"],
    python_requires=">=3.8",
)
