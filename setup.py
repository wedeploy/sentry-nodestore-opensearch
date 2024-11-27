from setuptools import setup, find_namespace_packages

install_requires = [
    'sentry==24.*',
    'opensearch-py==2.*',
]

with open("README.md", "r") as readme:
    long_description = readme.read()

setup(
    name='sentry-nodestore-opensearch',
    version='1.0.0',
    author='info@wedeploy.pl',
    author_email='info@wedeploy.pl',
    url='https://github.com/wedeploy/sentry-nodestore-opensearch',
    description='Sentry nodestore OpenSearch backend',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_namespace_packages(),
    include_package_data=True,
    license='Apache-2.0',
    install_requires=install_requires,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
    ],
    project_urls={
        'Bug Tracker': 'https://github.com/wedeploy/sentry-nodestore-opensearch/issues',
        'CI': 'https://github.com/wedeploy/sentry-nodestore-opensearch/actions',
        'Source Code': 'https://github.com/wedeploy/sentry-nodestore-opensearch',
    },
    keywords=['sentry', 'opensearch', 'nodestore', 'backend'],
)