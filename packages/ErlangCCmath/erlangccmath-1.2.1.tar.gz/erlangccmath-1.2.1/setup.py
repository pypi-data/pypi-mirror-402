from setuptools import setup,find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
# Get the long description from the README file
long_description = (here / "README.txt").read_text(encoding="utf-8")

# specify requirements of your package here
REQUIREMENTS = ['requests','tabulate']
  
# some more details
CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    "Operating System :: OS Independent",
    'License :: OSI Approved :: MIT License',
    "Programming Language :: Python :: 3",
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    ]
  
# calling the setup function 
setup(name='ErlangCCmath',
      version='1.2.1',
      license='MIT',
      description='Erlang C, X, and Chat Functions for Python',
      url='https://github.com/ccmath/erlang/Erlang_Python',
      author='K. Berkan Arik',
      author_email='support@ccmath.com',
      packages=find_packages(),
      classifiers=CLASSIFIERS,
      install_requires=REQUIREMENTS,
      long_description=long_description,
      keywords='erlang, erlang c, erlang x, erlang chat',
      python_requires='>=3'
      )
