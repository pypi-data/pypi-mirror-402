import setuptools as st
from pathlib import Path

with open(Path(__file__).parent / "README.md", "r", encoding="utf-8") as f:
    long_desc = f.read()

st.setup(
    name="ptk-blinkfix",
    version="1.0.1",
    author="Ahmet Altin",
    author_email="me@ahmetaltin.com",
    description="Blinking cursor fix for Python prompt_toolkit apps",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    license="BSD-3-Clause",
    url="https://github.com/ahmetaltin/ptk-blinkfix",
    packages=st.find_packages(),
    python_requires=">=3.7",
    install_requires=["prompt_toolkit>=3.0.0"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,  # Ensures MANIFEST.in files are included
)
