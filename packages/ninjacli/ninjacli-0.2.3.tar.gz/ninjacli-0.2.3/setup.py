from setuptools import setup, find_packages

setup(
    name='ninjacli', 
    version='0.2.3',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "openai>=2.15.0",
        "pydantic>=2.12.5",
        "python-dotenv>=1.2.1",
        "readchar>=4.2.1",
        "requests>=2.32.5",
        "rich>=14.2.0",
        "setuptools>=80.9.0",
        "twine>=6.2.0",
        "wheel>=0.45.1",
    ],
    entry_points={
        'console_scripts': [
            'ninjacli=ninjacli.main:main',
        ],
    },
    python_requires='>=3.10',
)