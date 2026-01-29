from setuptools import setup,find_packages
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="UnitCvrt",
    version="0.1.4",
    description="Unit Conversion System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Shinsuke Sakai",
    author_email='sakaishin0321@gmail.com',
    packages=find_packages(),
    install_requires=[
        "numpy>=2.0.2",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license='MIT',
    python_requires='>=3.6',
)