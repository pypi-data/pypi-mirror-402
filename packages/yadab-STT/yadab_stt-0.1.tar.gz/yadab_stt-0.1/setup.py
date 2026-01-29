from setuptools import setup, find_packages

setup(
    name='yadab_STT',
    version='0.1',
    author='YadabRokka',
    author_email='rokkabibash1@gmail.com',
    description='this is speech to text package created by yadab rokka',
    packages=find_packages(),
)
install_requirements = [
    'selenium',
    'webdriver-manager'
]