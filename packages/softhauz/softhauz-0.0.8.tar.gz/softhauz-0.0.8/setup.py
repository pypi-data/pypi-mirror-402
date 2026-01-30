from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    description = f.read()

setup(
    name='softhauz',
    version='0.0.8',
    author='Karen Urate',
    author_email='karen.urate@softhauz.ca',
    packages=find_packages(),
    install_requires=[
        'matplotlib==3.10.7',
        'numpy>=1.26.2',
        'sympy==1.14.0',
        'chempy>=0.10.1',
        'Faker>=35.2.0',
        'django-countries==7.6.1',
        'django-auto-logout==0.5.1',
        'python-dotenv==1.0.1',

    ],
    long_description=description,
    long_description_content_type="text/markdown",
)