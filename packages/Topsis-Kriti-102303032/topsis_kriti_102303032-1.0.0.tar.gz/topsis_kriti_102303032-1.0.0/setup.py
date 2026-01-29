from setuptools import setup, find_packages

setup(
    name="Topsis-Kriti-102303032",
    version="1.0.0",
    author="Kriti",
    author_email="kritigoyal0108@email.com",
    description="TOPSIS implementation using Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        'console_scripts': [
            'topsis=topsis_kriti_102303032.topsis:topsis'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
