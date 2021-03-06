import os
from setuptools import find_packages, setup


# Build README info
short_description = 'A python module that performs verification for Open Badges.'
try:
    import pypandoc
    pypandoc.convert_file('README.md', 'rst', outputfile='README.rst')
    with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
        README = readme.read()
except (ImportError, RuntimeError, OSError):
    README = short_description

# import VERSION
try:
    execfile(os.path.join(os.path.dirname(__file__), 'openbadges/version.py'))
except NameError:
    exec(open(os.path.join(os.path.dirname(__file__), 'openbadges/version.py')).read())

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


setup(
    name='badgecheck',
    version=".".join(map(str, VERSION)),
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    license='Apache 2',
    description=short_description,
    long_description=README,
    url='https://github.com/idGain/badgecheck',
    author='IMS Global',
    author_email='openbadgesinfo@imsglobal.org',
    classifiers=[
        'Environment :: Console',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Education',
        'Topic :: Utilities',
        'Intended Audience :: Developers'
    ],
    install_requires=[
        'aniso8601>=1.2.0',
        'Click >= 8',
        'future>=0.16.0',
        'jsonschema==4.2.1',
        'language-tags==1.1.0',
        'openbadges-bakery>=2.0.0',
        'puremagic==1.11',
        'pycryptodome==3.11.0',
        'pydux==0.2.2',
        'PyLD==2.0.3',
        'python-jose==3.3.0',
        'python-mimeparse==1.6.0',
        'pytz==2021.3',
        'requests >= 2.13',
        'requests_cache>=0.4.13',
        'rfc3986==1.5.0',
        'validators==0.18.2',
    ],
    extras_require={
        'server':  ["Flask==2.0.2", 'gunicorn==20.1.0'],
    },
    entry_points="""
        [console_scripts]
        openbadges=openbadges.command_line:cli
    """
)
