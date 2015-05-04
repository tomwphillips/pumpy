try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'name': 'pumpy',
    'version': '1.1.2',
    'description': 'Python RS-232 interface for Harvard syringe pumps',
    'url': 'https://github.com/tomwphillips/pumpy',
    'author': 'Tom W Phillips',
    'author_email': 'me@tomwphillips.co.uk',
    'license': 'MIT',
    'install_requires': ['pyserial>=2.7'],
}

setup(classifiers=[
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Topic :: Scientific/Engineering'],
        **config)
