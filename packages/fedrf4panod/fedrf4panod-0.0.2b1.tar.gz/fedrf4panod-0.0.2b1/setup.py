from setuptools import setup, find_packages
from pathlib import Path

# Read the long description from README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="fedrf4panod",
    version="0.0.2b1",
    packages=find_packages(),
    url="https://gitlab.gwdg.de/cdss/fairpact/fedrf4panod_pip",
    project_urls={
        "Bug Tracker": "https://gitlab.gwdg.de/cdss/fairpact/fedrf4panod_pip/-/issues",
        "Documentation": "https://gitlab.gwdg.de/cdss/fairpact/fedrf4panod_pip",
        "Source Code": "https://gitlab.gwdg.de/cdss/fairpact/fedrf4panod_pip",
        "Publication": "https://arxiv.org/abs/2405.20738",
    },
    license="MIT",
    author="Amirreza Aleyasin, Youngjun Park, Cord Schmidt, Lion Philip Wolf",
    author_email="amirreza.alise@gmail.com",
    description="Federated Random Forest for partially non-overlapping features across distributed sites",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=[
        "federated-learning",
        "random-forest",
        "machine-learning",
        "distributed-learning",
        "privacy-preserving",
        "healthcare-ai",
        "non-overlapping-features",
        "scikit-learn",
        "ensemble-learning",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "numpy >= 1.26.1",
        "pandas >= 1.5.3",
        "scikit-learn >= 1.3.2",
    ],
    python_requires=">=3.9",
    include_package_data=True,
)
