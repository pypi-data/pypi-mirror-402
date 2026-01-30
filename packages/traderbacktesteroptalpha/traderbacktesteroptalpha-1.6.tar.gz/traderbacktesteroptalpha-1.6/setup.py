from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='traderbacktesteroptalpha',
    version='1.6',
    description='Package for backtesting trading strategies and updating required files',
    author='Vadlamani Rampratap Sharma',
    author_email='rampratap.optalpha@gmail.com',
    packages=find_packages(),
    install_requires=[
        'pandas_ta==0.3.14b0',
        'swifter==1.3.4',
        'openpyxl==3.1.2',
        'ta==0.10.2',
        'pandas==1.5.3',
        'numpy==1.23.5'
    ],
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="MIT",
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9.7',
    include_package_data=True
)