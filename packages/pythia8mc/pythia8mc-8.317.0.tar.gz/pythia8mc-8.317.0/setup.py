readme = """
![](https://cernbox.cern.ch/remote.php/dav/public-files/t3FI2QHkue2MeXF/banner.png?scalingup=0&preview=1&a=1&c=385579588413030400%3Abb589188&x=1280&y=1280) 

# PYTHIA

PYTHIA is a program for the generation of high-energy physics collision events, i.e. for the description of collisions at high energies between electrons, protons, photons and heavy nuclei. It contains theory and models for a number of physics aspects, including hard and soft interactions, parton distributions, initial- and final-state parton showers, multiparton interactions, fragmentation and decay. It is largely based on original research, but also borrows many formulae and other knowledge from the literature. As such it is categorized as a general purpose Monte Carlo event generator.

# Installation

The PYTHIA package is natively written in C++, which is the preferred interface. To work with PYTHIA via C++ go to the [PYTHIA homepage](https://pythia.org/) and follow the instructions outlined there. The Python interface to PYTHIA can be installed directly via `pip`. **Note that for this PyPI distribution of PYTHIA, the module name has been changed from `pythia8` to `pythia8mc` as the `pythia8` project name was unavailable.** Outside of the PyPI distribution, the `pythia8` module name is always used.

```bash
pip install pythia8mc
```

The interface is also available via `conda`.

```bash
conda install -c conda-forge pythia8
```

It is possible, and in many ways preferable, to build the Python interface directly from the PYTHIA C++ distribution (as well as update the Python bindings) using the configuration script.

```bash
wget https://pythia.org/download/pythia83/pythia8XXX.tgz
tar xvfz pythia8XXX.tgz
cd pythia8XXX
./configure --with-python
make
```

# Usage

For a full description of usage, as well as examples, see the accompanying [HTML manual](https://pythia.org/documentation/) for this version of PYTHIA. 

The following imports the `pythia8mc` module and creates a `Pythia` instance.

```python
import pythia8mc
pythia = pythia8mc.Pythia()
```

PYTHIA must then be configured and initialized, in this example to produce minimum bias events at the LHC.

```python
pythia.readString("SoftQCD:all = on")
pythia.init()
```

Finally, we can produce an event, and explore the event record.

```python
pythia.next()
for prt in pythia.event: print(prt.name())
```

# Paths

PYTHIA requires the XML files which are used to build the [HTML manual](https://pythia.org/documentation/) to define settings. Additionally, settings files for tunes are also distributed with PYTHIA. For the PyPI distribution, these files can be found along the relative path,

```
../../../share/Pythia8/xmldoc
```

with respect to the `pythia8mc` module library. By default, this path should be correctly set, but it can be printed as follows.

```python
print(pythia8mc.__file__.rstrip("pythia8mc.so") + "../../../share/Pythia8/xmldoc")
```

The settings directory can be found in `../settings/` with respect to this folder. However, it is possible to overwrite the XML path by setting the environment variable `PYTHIA8DATA`,

```bash
export PYTHIA8DATA=<PYTHIA XML path> 
```

or by passing the XML path to the `Pythia` constructor.

```python
pythia8mc.Pythia("<PYTHIA XML path>")
```
"""
# setup.py is a part of the PYTHIA event generator.
# Copyright (C) 2026 Torbjorn Sjostrand.
# PYTHIA is licenced under the GNU GPL v2 or later, see COPYING for details.
# Please respect the MCnet Guidelines, see GUIDELINES for details.
# Author: Philip Ilten, August 2023.
#
# This script is used to package Pythia for PyPI.

#==========================================================================

# Define the Pythia version, the Python package subversion, and
# whether to include debug symbols.
ver = "317"
sub = "0"
dbg = False

#==========================================================================
def walk(top, pre):
    """
    Return a data structure for setup's data_files argument of the form,
    [(path, [files]), ...] for each non-empty directory.

    top: top directory to begin listing the data files.
    pre: prefix to append at the start of each relative path.
    """
    import os
    data, pre , top = [], pre.rstrip("/") + "/", top.rstrip("/") + "/"
    for path, subs, files in os.walk(pre):
        if not files: continue
        path += "/"
        data += [(top + path[len(pre):], [path + name for name in files])]
    return data

#==========================================================================

# Configure the Python build.

# Determine the PyBind version to use.
import sys
if sys.version_info.major >= 3 and sys.version_info.minor > 5:
    pybind = "2.10.4"
else:
    pybind = "2.9.2"

# Determine the package data (headers only needed for source).
data = walk("share/Pythia8", "pythia8" + ver + "/share/Pythia8")
if "sdist" in sys.argv:
    data += walk("include", "pythia8" + ver + "/plugins/python/include")

# Set the source files.
from glob import glob
sources = glob("pythia8" + ver + "/src/*.cc") + glob(
    "pythia8" + ver + "/plugins/python/src/*.cpp")

# Configure the build.
from distutils.core import Extension
ext = Extension(
    name="pythia8mc",
    language = "c++",
    define_macros = [
        # Enable GZIP support.
        ("GZIP", ""),
        # Set a dummy XML path. 
        ("XMLDIR", "\"share/Pythia8/xmldoc\""),
        # FastJet multithreading support.
        ("FJCORE_HAVE_LIMITED_THREAD_SAFETY", "")],
    extra_compile_args = ["-std=c++11"],
    extra_link_args = ["-lz"] + ([] if dbg else ["-Wl,-s"]),
    include_dirs = [
        "pythia8" + ver + "/plugins/python/include",
        "pythia8" + ver + "/plugins/python/include/" + pybind],
    sources = sources
)

# Class to remove compiler warnings.
from distutils.command.build_ext import build_ext
from distutils.sysconfig import customize_compiler
class RemoveWarnings(build_ext):
    def build_extensions(self):
        customize_compiler(self.compiler)
        for flag in [
                "-Wall", "-Wunused-but-set-variable", "-Wstrict-prototypes"]:
            try: self.compiler.compiler_so.remove(flag)
            except (AttributeError, ValueError): continue
        build_ext.build_extensions(self)

# Set up.
from distutils.core import setup
url = "https://pythia.org"
setup(
    name = "pythia8mc",
    version = ".".join(["8", ver, sub]),
    author = "Pythia 8 Team",
    author_email = "authors@pythia.org",
    description = "General purpose particle physics Monte Carlo generator.",
    long_description = readme,
    long_description_content_type = "text/markdown",
    license = "GNU GPL v2 or later",
    data_files = data,
    url = url,
    download_url = "%s/download/pythia83/pythia8%s.tgz" % (url, ver),
    project_urls = {
        "Documentation": "%s/manuals/pythia8%s/Welcome.html" % (url, ver),
        "Physics Manual": "%s/pdfdoc/pythia8300.pdf" % url,
        "Doxygen": "%s/doxygen/pythia8%s/" % (url, ver),
        "Issue Desk": "https://gitlab.com/Pythia8/releases/-/issues",
        "Source Repository": "https://gitlab.com/Pythia8/releases"
    },
    platforms = ["Linux", "MacOS"],
    # Don't allow zipping.
    zip_safe = False,
    # Define the C++ module.
    ext_modules = [ext],
    # Remove compiler warnings.
    cmdclass = {'build_ext': RemoveWarnings}
)
