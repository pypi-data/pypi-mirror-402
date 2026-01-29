"""Setup"""

import io

from setuptools import find_packages, setup

# Get packages from requirements.txt
with io.open("requirements.txt", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="goxlrutilityapi",
    version="1.2.5",
    description="GoXLR Utility API",
    keywords="GoXLR Utility API",
    author="Aidan Timson (Timmo)",
    author_email="aidan@timmo.dev",
    license="MIT",
    url="https://github.com/timmo001/goxlr-utility-api-py",
    packages=find_packages(exclude=["tests", "generator"]),
    install_requires=requirements,
)
