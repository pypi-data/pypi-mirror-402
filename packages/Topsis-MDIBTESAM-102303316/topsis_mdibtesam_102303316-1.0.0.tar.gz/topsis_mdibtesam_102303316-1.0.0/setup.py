from setuptools import setup, find_packages

setup(
    name="Topsis-MDIBTESAM_102303316",   # replace later with your real roll number
    version="1.0.0",
    author="mdibtesam",
    author_email="mibtesam267@gmail.com",
    description="TOPSIS implementation using Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main"
        ]
    },
)
