from setuptools import setup, find_packages

setup(
    name="db-shifter",
    version="0.1.9",
    packages=find_packages(),
    install_requires=[
        "psycopg2-binary",
    ],
    entry_points={
        "console_scripts": [
            "db-shifter=db_shifter.__main__:main"
        ]
    },
    author="superman",
    author_email="goodnesskolapo@gmail.com",
    description="A smart tool to sync missing rows between two PostgreSQL databases.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/goodness5/db-shifter",
    project_urls={
        "Changelog": "https://github.com/goodness5/db-shifter/blob/master/CHANGELOG.md",
        "Source": "https://github.com/goodness5/db-shifter",
        "Tracker": "https://github.com/goodness5/db-shifter/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
