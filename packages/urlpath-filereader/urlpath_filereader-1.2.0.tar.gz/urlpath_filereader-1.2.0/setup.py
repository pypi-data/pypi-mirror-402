from pip_setuptools import setup, find_packages, requirements, clean, readme

clean()
setup(
    name='urlpath-filereader',
    version='1.2.0',
    packages=find_packages(),
    install_requires=requirements(),
    author="Маг Ильяс DOMA (MagIlyasDOMA)",
    author_email='magilyas.doma.09@list.ru',
    url='https://github.com/MagIlyasDOMA/urlpath-filereader',
    python_requires='>=3.10',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    description='urlpath-filereader - библиотека для чтения файлов из локальной файловой системы и URL-адресов',
    long_description=readme(),
    long_description_content_type='text/markdown',
)
