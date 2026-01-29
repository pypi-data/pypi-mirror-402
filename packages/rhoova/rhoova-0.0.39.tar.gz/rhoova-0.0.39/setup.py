from setuptools import setup

setup(
    name='rhoova',
    packages=['rhoova'],
    version='0.0.39',
    license='MIT',
    description='Rhoova Client',
    author='Ekinoks Software',
    author_email='ali.turan@ekinokssoftware.com',
    # url='https://github.com/user/reponame',
    # download_url='https://github.com/user/reponame/archive/v_01.tar.gz',
    keywords=['RHOOVA', 'CLIENT'],
    install_requires=[
        'requests'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'
    ],
)
