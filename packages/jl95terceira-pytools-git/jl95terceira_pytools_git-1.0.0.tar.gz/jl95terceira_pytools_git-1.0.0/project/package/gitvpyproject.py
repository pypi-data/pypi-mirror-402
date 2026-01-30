import os
import os.path
import tomllib
import xml.etree.ElementTree as et

from jl95.pytools import gitv as _gitv

def _get_version(wd:str):

    with open(os.path.join(wd,'pyproject.toml'),'rb') as f:
        
        return tomllib.load(f)['project']['version']

def _get_version_and_print(wd:str):

    version = _get_version(wd)
    print('Python PyProject project version: '+version)
    #sha256={path: hashf.Hasher(hashlib.sha256).of(os.path.join(wd,path)) for path in ('pom.xml','src')}
    return version

def main():

    _gitv.main_given_version(description='Version a Python PyProject project with a git tag\nThe version number will be read from the project file (pyproject.toml).',
                             version_getter=lambda wd,agetter: _get_version_and_print(wd))

if __name__ == '__main__': main()
