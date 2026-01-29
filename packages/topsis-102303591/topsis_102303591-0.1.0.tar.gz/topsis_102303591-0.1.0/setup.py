from setuptools import setup, find_packages

setup(
    name='topsis-102303591',  # ✅ MUST contain your roll number
    version='0.1.0',
    author='Lakshya Arora',
    author_email='lakshya8725@gmail.com',
    description='Python implementation of TOPSIS for multi-criteria decision making',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Lakshya8725/Topsis-package',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)


