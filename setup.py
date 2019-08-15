from setuptools import setup, find_packages


setup(
    name='firefly',
    version='0.0.3',
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
        'h5pyd @ git+https://github.com/HDFGroup/h5pyd.git@master#egg=h5pyd',
        'ipyleaflet>=0.11.1'
    ],
    scripts=[
        'scripts/ch10-to-h5.py',
        'scripts/ch10summary.py',
        'scripts/derive-6dof.py'
    ],
    package_data={'': ['FY18_MIRTA_Points.csv']}
)
