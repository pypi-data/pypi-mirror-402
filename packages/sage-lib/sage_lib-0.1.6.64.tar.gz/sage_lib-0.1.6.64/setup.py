from setuptools import setup, find_packages

extras = {
    'analysis': [
        'scipy>=1.7.0',
    ],
    'dev': [
        'pytest>=6.0',  # Specified minimum version for compatibility
        'flake8>=3.8',
        'black',  # Added black for code formatting
        'mypy',  # Added mypy for type checking
        'coverage',  # Added for code coverage analysis
        'tox',  # Added for testing across multiple environments
    ],
    'docs': [
        'sphinx>=4.0',
        'sphinx-rtd-theme>=0.5.0',
        'myst-parser',  # Added MyST parser for enhanced Markdown support in Sphinx
        'sphinx-autodoc-typehints',  # Added for better type hint documentation
    ],
    'ml': [
        'scikit-learn>=0.24.0',
        'umap-learn>=0.5.0',
        'kneed>=0.7.0',
        'hdbscan>=0.8.0',
        'dscribe',
    ],
    'viz': [
        'matplotlib>=3.4.0',
        'seaborn>=0.11.0',
        'imageio>=2.10.0',
        'glfw',
        'PyOpenGL',
        'PyOpenGL_accelerate',
        'imgui[glfw]',
        'Pillow',
    ],
}

# Automatically combine all extras into 'all'
extras['all'] = sorted(list(set(dep for deps in extras.values() for dep in deps)))

setup(
    name='sage_lib',  # El nombre del paquete
    version='0.1.6.64',
    description='A library for advanced scientific calculations and visualization',
    long_description=open('README.md', encoding='utf-8').read(),  # Updated to specify encoding for better compatibility
    long_description_content_type='text/markdown',
    author='Lombardi, Juan Manuel',
    author_email='lombardi@fhi-berlin.mpg.de',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    license='MIT',
    install_requires=[
        'numpy>=1.21.0',  # Updated to a more recent version for better compatibility
        'tqdm>=4.50.0',
        'joblib>=1.0.0',
        'h5py>=3.6.0',
    ],
    extras_require=extras,
    entry_points={
        'console_scripts': [
            'sage = sage_lib.main:main',  # Establece 'sage' como el comando de consola
        ],
    },
    keywords='scientific calculations visualization computational chemistry quantum mechanics machine learning data analysis',  # Expanded keywords for better discoverability
    #project_urls={
    #    'Bug Reports': '',
    #    'Source': '',
    #    'Documentation': '',  # Added a link to documentation
    #},
)
