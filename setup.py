import os

readme = os.path.join(os.path.dirname(__file__), 'README.rst')
long_description = open(readme).read()


SETUP_ARGS = dict(
    name='django-flowr',
    version='0.1.2',
    description='Django based dynamic state machine system',
    long_description=long_description,
    url='https://github.com/cltrudeau/django-flowr',
    author='Christopher Trudeau',
    author_email='ctrudeau+pypi@arsensa.com',
    license='MIT',
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='django,state machine',
    install_requires=[
        'Django>=1.8',
    ],
)

if __name__ == '__main__':
    from setuptools import setup, find_packages

    SETUP_ARGS['packages'] = find_packages()
    setup(**SETUP_ARGS)
