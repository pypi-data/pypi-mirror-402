from setuptools import setup, find_packages
setup(
  name="Topsis-RishabhSharma-102303286",
  version="1.0",
  packages=find_packages(), # includes all folders including __int__.py files as it defines a folder a package
  install_requires=["pandas","numpy"],
  entry_points={
    "console_scripts":[
      "topsis=topsis.topsis:main" # we define topsis a command which will run topsis.topsis.py then call the main function
    ]
  },
  author="Rishabh Sharma",
  description="TOPSIS implementation",
  long_description=open("README.md").read(),
  long_description_content_type="text/markdown",
)