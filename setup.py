from setuptools import setup


def get_from_requirements():
    with open('requirements.txt', 'r') as fp:
        reqs = [r.strip() for r in fp.readlines()]
        reqs = [r for r in reqs if r and not r.startswith('#')]

    return reqs


setup(
    name='PROJECTNAME',
    version='1.0',
    description='',
    author='',
    author_email='',
    url='',
    install_requires=get_from_requirements(),
)
