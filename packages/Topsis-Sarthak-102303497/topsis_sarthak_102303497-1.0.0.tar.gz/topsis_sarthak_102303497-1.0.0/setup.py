from setuptools import setup, find_packages

setup(
    name='Topsis-Sarthak-102303497',
    version='1.0.0',
    author='Sarthak Gaba',
    author_email='your.email@example.com',
    description='A Python package for TOPSIS multi-criteria decision analysis',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/Topsis-Sarthak-102203628',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
    ],
    entry_points={
        'console_scripts': [
            'topsis=topsis_pkg.topsis:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
