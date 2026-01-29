from setuptools import setup, find_packages, Extension
 
classifiers = [
  'Development Status :: 5 - Production/Stable',
  'Intended Audience :: Education',
  'Operating System :: Microsoft :: Windows :: Windows 10',
  'License :: OSI Approved :: MIT License',
  'Programming Language :: Python :: 3'
]
 
setup(
  name='gchatUts',
  version='1.0.0',
  description='Lib para comunicação via Google Chat Web Hook',
  long_description=open('README.md',encoding='utf-8').read() + '\n\n' + open('CHANGELOG.txt').read(),
  long_description_content_type='text/markdown',
  url='',  
  author='Zdek',
  author_email='',
  license='MIT', 
  classifiers=classifiers,
  keywords='gChat', 
  packages=find_packages(),
  install_requires=[
     'requests>=2.7.0'
  ]
)
