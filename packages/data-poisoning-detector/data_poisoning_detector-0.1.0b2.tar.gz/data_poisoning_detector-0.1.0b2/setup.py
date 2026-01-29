from setuptools import setup, find_packages

classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'Operating System :: Microsoft :: Windows :: Windows 10',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.11',
]

setup(
    name='data-poisoning-detector',
    version='0.1.0b2',
    description='Data Poisoning Detection using self-supervised learning techniques',
    long_description=open('README.md').read() + '\n\n' + open('CHANGELOG.txt').read(),
    url='',
    author='Lakshan Costa',
    author_email='lakshancosta2@gmail.com',
    license='MIT',
    classifiers=classifiers,
    keywords='data poisoning, self-supervised learning, machine learning, security',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
        'scikit-learn',
        'flask',
        'torch',
        'torchvision',
    ],
)