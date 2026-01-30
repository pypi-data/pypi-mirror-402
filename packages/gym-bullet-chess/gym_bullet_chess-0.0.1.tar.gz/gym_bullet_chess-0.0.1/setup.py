from pathlib import Path
from setuptools import setup, find_packages

long_description = Path("README.md").read_text(encoding="utf-8")

setup(
    name="gym_bullet_chess",
    version="0.0.1",
    description="Gymnasium-compatible bullet chess environment with real-time constraints.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ChoiCube84",
    author_email="wldnd0804@gmail.com",
    url="https://github.com/ChoiCube84/gym-bullet-chess",
    project_urls={
        "Source": "https://github.com/ChoiCube84/gym-bullet-chess",
        "Issues": "https://github.com/ChoiCube84/gym-bullet-chess/issues",
    },
    license="GPL-3.0-or-later",
    license_files=["LICENSE"],
    python_requires=">=3.8",
    packages=find_packages(),
    include_package_data=True,
    package_data={"gym_bullet_chess": ["assets/*.png"]},
    install_requires=["gymnasium>=1.0.0", "chess>=1.10.0", "numpy>=1.24.0"],
    extras_require={"gui": ["pygame"], "render": ["Pillow"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Games/Entertainment :: Board Games",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="gymnasium reinforcement-learning chess bullet",
)
