from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="bfk-authsystem",
    version="1.2.3",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'bfk_authsystem': ['docs/*.md', 'docs/*.py'],
    },
    install_requires=[
        "requests>=2.31.0",
        "cryptography>=41.0.0",
    ],
    extras_require={
        "ui": ["PyQt5>=5.15.0"],
        "hardware": ["psutil>=5.9.0"],
        "full": ["PyQt5>=5.15.0", "psutil>=5.9.0"],
    },
    author="BFK Engenharia",
    author_email="bruno@bfk.eng.br",
    description="Biblioteca cliente para integracao com BFK AuthSystem",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bfkons/BFK-AuthSystem",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    keywords="license, authentication, mfa, security",
)
