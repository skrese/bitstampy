from setuptools import setup

setup(
    name='bitstampy',
    author='https://github.com/unwitting',
    author_email='jackprestonuk@gmail.com',
    packages=['bitstampy'],
    scripts=['bin/api_runthrough.py'],
    url='https://github.com/unwitting/bitstampy',
    license='LICENSE.txt',
    description='Bitstamp API wrapper for Python',
    long_description=open('README.txt').read(),
    python_requires=">=3.8.5",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Internet :: WWW/HTTP'
    ],
    install_requires=['requests']
)
