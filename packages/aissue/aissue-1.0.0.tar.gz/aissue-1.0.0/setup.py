from setuptools import setup, find_packages
import os

def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except FileNotFoundError:
        return ""

setup(
    name='aissue',
    version='1.0.0',
    author='AIssue Team',
    author_email='support@aissue.com',
    description='Django middleware for AIssue error monitoring',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/aissue/aissue-django',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Framework :: Django :: 4.2',
    ],
    python_requires='>=3.8',
    install_requires=[
        'Django>=3.2',
        'requests>=2.25.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-django>=4.0',
            'black>=21.0',
            'flake8>=3.8',
        ]
    },
    keywords='django middleware error monitoring aissue',
    project_urls={
        'Bug Reports': 'https://github.com/aissue/aissue-django/issues',
        'Source': 'https://github.com/aissue/aissue-django',
        'Documentation': 'https://docs.aissue.com/django',
    },
) 