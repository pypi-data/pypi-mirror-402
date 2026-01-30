from setuptools import setup, find_packages

setup(
    name="django-pulse",
    version="1.0.1",
    author="Jesus M.",
    description="Backend sync engine for pulse-rn",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/JesusM15/django-pulse",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "django>=3.2",
        "channels>=3.0",
        "channels-redis>=3.0",
        "asgiref>=3.3",
    ],
    classifiers=[
        "Framework :: Django",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)