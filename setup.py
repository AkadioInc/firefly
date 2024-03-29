from setuptools import setup, find_packages


setup(
    name='firefly',
    version='0.0.5',
    description='Scripts and modules for the FIREfly project',
    long_description='To be provided.',
    long_description_content_type='text',
    url='TBA',
    author='Akadio Inc',
    author_email='admin@akadio.com',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    python_requires='>=3.7, <4',
    install_requires=[
        'h5py>=2.9',
        'h5pyd>=0.8.4',
        'ipyleaflet>=0.11.1',
        'hvplot>=0.4'
    ],
    scripts=[
        'scripts/ch10-to-h5.py',
        'scripts/ch10summary.py',
        'scripts/derive-6dof.py'
    ],
    package_data={'': ['FY18_MIRTA_Points.csv']}
)
