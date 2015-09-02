from setuptools import setup, find_packages
from version import VERSION

setup(
    name='django-flowr',
    version=VERSION,
    description='Django based dynamic state machine system',
    long_description=(
        'Most state machine libraries are "static" and require the flow '
        'in the state machine to be definied programmatically.  Flowr '
        'is designed so that you can build state machine flows and '
        'store them in a database.  There are two key concepts: rule '
        'graphs and state machines.  The programmer defines one or more '
        'sets of rules that describe the allowed flow between states, '
        'the user can then use the GUI tools to construct state '
        'machines that follow these rules and store the machines in the '
        'database.  The state machines can then be instantiated for '
        'processing the flow which triggers call-back mechanisms in the '
        'rule objects on entering and leaving a state. '
    ),
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
    packages=find_packages(),
    install_requires=[
        'Django>=1.8',
    ],
)
