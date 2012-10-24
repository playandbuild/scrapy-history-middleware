try:
    from setuptools import setup
except ImportError:
    from distutils import setup

import history


packages = [
    'history',
]

requires = [
    'scrapy>=0.12,<=0.12.99',
    'boto',
    'parsedatetime',
]

setup(
    name='history',
    version=history.__version__,
    description='Scrapy downloader middleware to enable persistent storage.',
    long_description=open('README.md').read(),
    author='Andrew Preston',
    author_email='andrew@preston.co.nz',
    url='http://github.com/playandbuild/scrapy-history-middleware',
    packages=packages,
    install_requires=requires,
    license=open('LICENSE').read(),
    classifiers=(
        'Development Status :: 4 - Beta'
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
    ),
)
