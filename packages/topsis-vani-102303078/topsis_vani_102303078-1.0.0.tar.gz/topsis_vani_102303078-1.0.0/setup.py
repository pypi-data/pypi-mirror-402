from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name='Topsis-Vani-102303078',
    version='1.0.0',
    author='Vani Goyal',
    author_email='vgoyal_be23@thapar.edu',
    description='A Python package for TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/vgalpha/Topsis-Vani-102303078',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
    ],
    keywords='topsis mcdm decision-making multi-criteria optimization ranking',
    install_requires=[
        'pandas>=1.0.0',
        'numpy>=1.18.0',
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'topsis=topsis_vani_102303078.topsis:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/vgalpha/Topsis-Vani-102303078/issues',
        'Source': 'https://github.com/vgalpha/Topsis-Vani-102303078',
    },
)
