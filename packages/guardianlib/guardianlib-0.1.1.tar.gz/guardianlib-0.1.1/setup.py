from setuptools import setup, find_packages

setup(
    name="guardianlib",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[],          
    author="ImLuni5",
    description="Python Library for FavortieGuardian",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/ImLuni5/GuardianLib-Py",
    python_requires='>=3.6',
)
