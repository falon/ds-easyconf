from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='ds-easyconf',
    version='1.1.0',
    description='Easy dsconf manager',
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="389ds rhds directory LDAP configuration config",
    scripts=['ds-easyconf.py'],
    packages=[],
    include_package_data = False,
    data_files=[
        ('/etc/ds-easyconf', ['ds-easyconf.yaml.dist']),
        ('/usr/share/doc/ds-easyconf', ['README.md']),
        ('/usr/share/licenses/ds-easyconf', ['LICENSE']),
    ],
    install_requires=[
        'PyYAML>3.11',
        'lib389>1.4.0'
    ],
    python_requires='>=3.6',
    url='https://github.com/falon/ds-easyconf',
    license='GNU General Public License v3.0',
    author='Marco Favero',
    author_email='m.faverof@gmail.com',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.6",
        "Topic :: System :: Systems Administration :: Authentication/Directory :: LDAP",
        "Topic :: Utilities"
    ]
)
