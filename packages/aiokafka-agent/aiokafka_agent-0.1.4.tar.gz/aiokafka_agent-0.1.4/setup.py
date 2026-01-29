from setuptools import find_packages, setup


setup(
    name="aiokafka-agent",
    version="0.1.4",
    packages=find_packages(exclude=["tests*"]),
    install_requires=["aiokafka", "pydantic>=2.0.0", "pydantic-settings>=2.0.0"],
    python_requires=">=3.9",
)
