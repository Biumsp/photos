from setuptools import setup

setup(
    name="photos",
    version="1.0",
    py_modules=["photos"],
    include_package_data=True,
    install_requires=["click"],
    entry_points="""
        [console_scripts]
        photos=photos:cli
    """,
)