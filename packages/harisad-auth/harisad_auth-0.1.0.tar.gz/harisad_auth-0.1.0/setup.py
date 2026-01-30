from setuptools import setup, find_packages

setup(
    name="harisad_auth",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "argon2-cffi>=21.1.0",
    ],
    author="Haris Mujianto", 
    description="Library Auth dengan Double Hashing Argon2id + HMAC-SHA512",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)