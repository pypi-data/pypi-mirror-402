
from setuptools import setup, find_packages

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Education',
    'Operating System :: Microsoft :: Windows',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3'
]
setup(
    name="umar_python_tools",
    version="0.0.1",
    packages=find_packages(),
    description="Simple math and text utility library",
    author="UMAR",
    license='MIT',
    classifiers=classifiers,
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.7"
)
