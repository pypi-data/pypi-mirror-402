from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='mydisct-solver',
    version='1.0.1',
    description='Official Python library for MyDisct Solver - Enterprise AI-Powered Captcha Solving Service with 20+ token types and 25+ image types',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='MyDisct Solver',
    author_email='support@solver.mydisct.com',
    url='https://github.com/mydisctsolver/MyDisct-Solver',
    project_urls={
        'Bug Tracker': 'https://github.com/mydisctsolver/MyDisct-Solver/issues',
        'Documentation': 'https://solver.mydisct.com/api-docs',
        'Homepage': 'https://solver.mydisct.com'
    },
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.0'
    ],
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Security'
    ],
    keywords='captcha solver recaptcha hcaptcha turnstile funcaptcha geetest cloudflare mydisct automation bot bypass',
    license='MIT'
)
