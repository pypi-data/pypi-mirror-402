from setuptools import setup, find_packages

setup(
    name="Topsis-Navya-102303313",
    version="1.0.0",
    author="Navya",
    author_email="navya@example.com",
    description="TOPSIS command line tool",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    entry_points={
        "console_scripts": [
            "topsis=TOPSIS_NAVYA_102303313.topsis:run"
        ]
    },
)
