from setuptools import setup, find_packages

setup(
    name="fedrf4panod",
    version="0.0.2",
    packages=find_packages(),
    url="https://gitlab.gwdg.de/cdss/fairpact/fedrf4panod_pip",
    license="MIT",
    author="Amirreza Aleyasin - Youngjun Park - Cord Schmidt - Lion Philip Wolf",
    author_email="amirreza.alise@gmail.com",
    description="Federated Random Forest for non overlapping features python package.",
    install_requires=["numpy >= 1.26.1", "pandas >= 1.5.3", "scikit-learn >= 1.3.2"],
    python_requires=">=3.9",
)
