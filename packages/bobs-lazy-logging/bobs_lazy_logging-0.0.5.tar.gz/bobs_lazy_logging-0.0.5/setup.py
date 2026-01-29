# type: ignore

from setuptools import find_packages, setup

setup(
    name='bobs_lazy_logging',
    packages=find_packages(),
    use_scm_version={
        "root": ".",
        "relative_to": __file__,
        "local_scheme": "no-local-version",
        "version_scheme": "python-simplified-semver",
    },
    description='Debug logging for lazy people',
    author='BobTheBuidler',
    author_email='bobthebuidlerdefi@gmail.com',
    url='https://github.com/BobTheBuidler/lazy_logging',
    license='MIT',
    python_requires=">=3.10,<4",
    install_requires=['typing_extensions>=4.4.0'],
    setup_requires=['setuptools_scm'],
)
