from setuptools import setup, Extension, find_packages
from setuptools.command.build_py import build_py
from Cython.Build import cythonize
import glob
import os

class CustomBuildPy(build_py):
    """
    Custom build command:
    1. Build all Cython extensions first.
    2. Remove original Python files in _internal (except __init__.py).
    """
    def run(self):
        super().run()
        internal_build_dir = os.path.join(self.build_lib, "conversational_graph", "_internal")

        if os.path.exists(internal_build_dir):
            for filename in os.listdir(internal_build_dir):
                # Only delete original .py files, keep __init__.py
                if filename.endswith(".py") and filename != "__init__.py":
                    os.remove(os.path.join(internal_build_dir, filename))

def get_extensions():
    """
    Compile all Python files in _internal into Cython extensions (.so)
    """
    internal_dir = os.path.join("conversational_graph", "_internal")
    sources = glob.glob(os.path.join(internal_dir, "*.py"))

    extensions = []
    for source in sources:
        # Module name: conversational_graph._internal.filename
        module_name = source.replace(os.path.sep, ".")[:-3]
        extensions.append(
            Extension(
                module_name,
                [source],
            )
        )
    return extensions


setup(
    name="videosdk-conversational-graph",
    version="0.0.5",
    packages=find_packages(include=["conversational_graph*"]),
    cmdclass={"build_py": CustomBuildPy},
    ext_modules=cythonize(
        get_extensions(),
        compiler_directives={"language_level": "3"},
        build_dir="build",
    ),
    include_package_data=True,
    python_requires=">=3.9",
    zip_safe=False, 
)
