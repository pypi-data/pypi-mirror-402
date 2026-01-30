"""
Setup script pour BMB
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bmb",
    version="1.0.0",
    author="Marouan Bouchettoy",
    author_email="marouanbouchettoy@gmail.com",
    description="BMB - Backend Framework utilisant BMDB ORM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BM-Framework/bmb",
    packages=find_packages(),
    include_package_data=True,  # This is crucial
    package_data={
        'bmb': ['project_template/**/*'],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Flask>=3.1.2",
        "flask-cors>=6.0.2",
        "PyJWT>=2.10.1",
        "python-dotenv>=1.2.1",
        "Werkzeug>=3.1.5",
        "bmdb>=1.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=9.0.2",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "postgresql": ["psycopg2-binary>=2.9.0"],
        "mysql": ["pymysql>=1.1.0"],
    },
    entry_points={
        "console_scripts": [
            "bmb=bmb.cli:main",
        ],
    },
)