from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='topsis-lavanya-102313066',
    version='1.0.1',
    description='TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) implementation for multi-criteria decision making',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Lavanya Garg',
    author_email='lgarg_be23@thapar.edu',
    url='https://github.com/lavanya-garg/topsis-lavanya-102313066',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Office/Business',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
    install_requires=[
        'pandas>=1.0.0',
        'numpy>=1.18.0',
    ],
    entry_points={
        'console_scripts': [
            'topsis-cli=topsis_lavanya_102313066.cli:main',
        ],
    },
    keywords='topsis mcdm decision-making multi-criteria',
    project_urls={
        'Bug Reports': 'https://github.com/lavanya-garg/topsis-lavanya-102313066/issues',
        'Documentation': 'https://github.com/lavanya-garg/topsis-lavanya-102313066',
        'Source Code': 'https://github.com/lavanya-garg/topsis-lavanya-102313066',
    },
    include_package_data=True,
    zip_safe=False,
)

