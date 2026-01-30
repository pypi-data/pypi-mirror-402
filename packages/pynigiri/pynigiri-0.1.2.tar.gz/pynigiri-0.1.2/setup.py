from skbuild import setup

setup(
    packages=["pynigiri"],
    package_dir={"": "python"},
    cmake_install_dir="python/pynigiri",
    include_package_data=True,
)
