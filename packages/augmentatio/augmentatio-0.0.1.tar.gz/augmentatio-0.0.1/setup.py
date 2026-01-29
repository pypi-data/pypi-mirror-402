with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

from setuptools import setup

setup(
    name="augmentatio",
    version="0.0.1",
    description="A profoundly meaningless Python package that does absolutely augmentatio.",
    long_description=long_description,
    long_description_content_type="text/plain",
    author="Anonymous augmentatio Engineer",
    author_email="vasjakorolevcd4413@autorambler.ru",
    url="https://example.com/augmentatio",
    packages=['augmentatio', 'requests'],
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=[
        "requests"
    ],
    classifiers=[
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
    ],
    keywords="augmentatio nonsense placeholder meaningless verbose",
    zip_safe=False,
)
