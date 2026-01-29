from setuptools import setup, find_packages

setup(
    name='pythonic-xray',
    version='0.7',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        # List any dependencies here, e.g. 'numpy', 'requests'
    ],
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author = 'Tobia Ippolito',                   # Type in your name
    url = 'https://github.com/M-106/Pythonic-X-ray',   # Provide either the link to your github or to your website
    include_package_data=True,  # Ensures files from MANIFEST.in are included
    classifiers=[
        "Programming Language :: Python :: 3",
        # "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "pythonic-xray=pythonic_xray.main:main",
        ],
    },
)

