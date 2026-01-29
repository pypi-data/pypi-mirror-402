from setuptools import setup, find_packages
import os

# Read the README file for long description
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
with open(readme_path, "r", encoding="utf-8") as fh:
	long_description = fh.read()

# Read the LICENSE file
license_path = os.path.join(os.path.dirname(__file__), "LICENSE")
license_text = "MIT License"
if os.path.exists(license_path):
	with open(license_path, "r", encoding="utf-8") as fh:
		license_text = fh.read().split("\n")[0]  # Get first line

setup(
	name="easy_custom_titlebar",
	version="2.0.1",  # Patch release: reliability improvements and bug fixes
	description="A plug-and-play custom title bar and window manager for Pygame/Win32 apps on Windows",
	long_description=long_description,
	long_description_content_type="text/markdown",
	author="Enazzzz",
	# author_email="",  # Add your email here if you want
	# url="https://github.com/yourusername/easy-custom-titlebar",  # Add your repo URL here
	license="MIT",
	packages=find_packages(),
	include_package_data=True,
	package_data={
		"easy_custom_titlebar": ["assets/*.png", "assets/*.ico"],
	},
	install_requires=[
		"pygame>=2.0.0",
		"pywin32>=300",
	],
	python_requires=">=3.7",
	classifiers=[
		"Development Status :: 4 - Beta",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: MIT License",
		"Operating System :: Microsoft :: Windows",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3.7",
		"Programming Language :: Python :: 3.8",
		"Programming Language :: Python :: 3.9",
		"Programming Language :: Python :: 3.10",
		"Programming Language :: Python :: 3.11",
		"Programming Language :: Python :: 3.12",
		"Topic :: Software Development :: Libraries :: Python Modules",
		"Topic :: Multimedia :: Graphics",
		"Topic :: Games/Entertainment",
	],
	keywords=[
		"pygame",
		"titlebar",
		"window",
		"custom",
		"win32",
		"gui",
		"window-manager",
		"borderless",
		"windows",
	],
	project_urls={
		# "Bug Reports": "https://github.com/yourusername/easy-custom-titlebar/issues",
		# "Source": "https://github.com/yourusername/easy-custom-titlebar",
		# "Documentation": "https://github.com/yourusername/easy-custom-titlebar#readme",
	},
) 