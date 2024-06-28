from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in eagle_automation_customization/__init__.py
from eagle_automation_customization import __version__ as version

setup(
	name="",
	version=version,
	description="Manages eagle Automation Customization",
	author="Aerele",
	author_email="hello@aerele.in",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
