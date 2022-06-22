from setuptools import setup, find_packages

setup(
    name="odoo-pms",
    version="0.0.1",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'odoo-pms = odoo_pms.cli:main'
        ]
    }
)
