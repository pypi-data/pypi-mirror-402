import setuptools
from pathlib import Path
gaiacmds_home = Path(__file__).parent
pypi_descrip = (gaiacmds_home / "README.md").read_text()

setuptools.setup(
	name = "gaiacmds",
	version = "0.5.1",
	author = "Ava Polzin",
	author_email = "apolzin@uchicago.edu",
	description = "Good enough CMDs based on simple star cluster member selection.",
	packages = ["gaiacmds"],
	url = "https://github.com/avapolzin/goodenough_gaia_cmds",
	license = "MIT",
	classifiers = [
		"Development Status :: 4 - Beta",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Programming Language :: Python"],
	python_requires = ">=3",
	install_requires = ["astropy", "astroquery", "matplotlib", "numpy", "pandas"],
	long_description=pypi_descrip,
    long_description_content_type='text/markdown'
)