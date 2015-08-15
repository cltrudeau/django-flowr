from setuptools import setup, find_packages

setup(
    name='django-flowr',
    version='0.1.0',
    description='Django based dynamic state machine system',
    long_description=('Stuff goes here'
        ),
#    url='https://github.com/cltrudeau/django-yacon',
    author='Christopher Trudeau',
    author_email='ctrudeau+pypi@arsensa.com',
#    license='MIT',
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
    packages=find_packages(),
    install_requires=[
        'Django>=1.8',
    ],
)
