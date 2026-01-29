import setuptools
from pathlib import Path

here = Path(__file__).resolve().parent

readme_path = here / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")
else:
    # Fallback so builds never hard-fail
    long_description = "DigitalArzEngine for GEE, raster and vector data processing"

# Requirements handling
requirement_path = here / "digitalarzengine" / "requirements-prod.txt"
skip_packages = {"pytest", "moto", "wheel", "twine"}
install_requires = []

print("requirement", requirement_path)

if requirement_path.is_file():
    for line in requirement_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if any(stripped.startswith(pkg) for pkg in skip_packages):
            continue
        install_requires.append(stripped)

print("installed requirements", install_requires)

# Setup definition
setuptools.setup(
    name="digitalarzengine",
    version='0.4.10',
    author="Ather Ashraf",
    author_email="atherashraf@gmail.com",
    description="DigitalArzEngine for GEE, raster and vector data processing",
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires='>=3.7',
    install_requires=install_requires,
    packages=setuptools.find_packages(exclude=["digitalarzengine.tests", "digitalarzengine.tests.*"]),
    include_package_data=True,
    keywords=['raster', 'vector', 'digital earth engine'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
