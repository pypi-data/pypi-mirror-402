from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


setup(
    name="bja_utils",
    version="0.1.6",
    author="Benton Anderson",
    description="Convenience functions for mass spectrometry proteomics & lipidomics analysis, parsing, statisticss, biological interpretation, and plotting.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    package_data={'plotting': ['*.mplstyle'],
                  'resources': ['*.json', '*.tsv']},
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=['pandas>=1.0.0',
                      'numpy>=1.20.0',
                      'matplotlib>=3.5.0',
                      'seaborn>=0.10.0',
                      'scipy>=1.11.0',
                      'statsmodels>=0.11.1',
                      'goatools>=1.5.1'],
    extras_require={
        'parsing': ['pygoslin'],
        'plotly_apps': ['plotly>6.0.0', 'dash-ag-grid>=32.3.2'],
        'all': ['pygoslin', 'plotly>6.0.0', 'dash-ag-grid>=32.3.2'], ## Don't forget to add any packages from the others here in extras_require
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
)