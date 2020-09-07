from setuptools import setup, find_packages


setup(
    name='payment',
    version='1.0',
    description='Payment plugin netbox, for control rent equipment',
    url='https://github.com/cbipoe3ka/custom-netbox/tree/master/netbox/payment',
    author='Alexandr Ovsyannikov',
    license='Apache 2.0',
    install_requires=[],
    package=find_packages(),
    include_package_data=True,
)