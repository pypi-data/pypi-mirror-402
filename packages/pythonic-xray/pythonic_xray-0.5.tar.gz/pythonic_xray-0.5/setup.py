from setuptools import setup, find_packages

setup(
    name='pythonic-xray',
    version='0.5',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        # List any dependencies here, e.g. 'numpy', 'requests'
    ],
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    include_package_data=True,  # Ensures files from MANIFEST.in are included
    classifiers=[
        "Programming Language :: Python :: 3",
        # "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

