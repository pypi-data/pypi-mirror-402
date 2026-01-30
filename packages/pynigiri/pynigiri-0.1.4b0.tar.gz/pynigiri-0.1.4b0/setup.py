from skbuild import setup

setup(
    packages=["pynigiri"],
    package_dir={"pynigiri": "pynigiri"},
    cmake_install_dir="pynigiri",
    include_package_data=True,
)
