from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ringtheory",
    version="1.0.73", 
    author="RingTheory AI",
    author_email="vipvodu@yandex.ru",
    description="Energy-efficient GPU/CPU computing using quantum-inspired ring patterns",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://arkhipsoft.ru/Article/ID?num=89",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: System :: Hardware",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.19.0",
        "psutil>=5.8.0",
    ],
    extras_require={
        "gpu": [
            "torch>=1.9.0",
        ],
        "mining": [
            "torch>=1.9.0",
        ],  # УБРАЛ pycuda - он сложный для установки
        "full": [
            "torch>=1.9.0",
            "matplotlib>=3.3.0",
            "pandas>=1.3.0",
        ]
    },
    keywords=[
        "energy-efficiency",
        "gpu-optimization",
        "crypto-mining",
        "quantum-computing",
        "ring-theory",
        "ai-optimization",
        "data-center",
    ],
    # УДАЛИЛ project_urls - они создают ненужные ссылки
    # Оставьте ТОЛЬКО если есть реальные сайты
    license="Proprietary",
)