from pip_setuptools import setup, clean, find_packages, requirements, readme

clean()
setup(
    name='python-package-downloader',
    version='1.1.3',
    packages=find_packages(),
    entry_points=dict(console_scripts=[
        'ppd=python_package_downloader:main',
        'python-package-downloader=python_package_downloader:main',
        'python_package_downloader=python_package_downloader:main'
    ]),
    install_requires=requirements(),
    author="Маг Ильяс DOMA (MagIlyasDOMA)",
    author_email='magilyas.doma.09@list.ru',
    url='https://github.com/MagIlyasDOMA/python-package-downloader',
    python_requires='>=3.10',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    description="A CLI application for easily downloading Python packages",
    long_description=readme(),
    long_description_content_type="text/markdown",
)
