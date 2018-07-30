from os import makedirs
from os.path import exists, join
from subprocess import call
from shutil import copyfile, rmtree, move
from zipfile import ZipFile
from hashlib import sha256 as _sha256

from yaml import load, dump


def import_yaml(yaml_file):
    '''
    Given a yaml_file path
    open and deserialize the doc
    return the data
    '''

    with open(yaml_file) as f:
        return load(f)

def export_yaml(yaml_file, contents):
    '''
    Given a yaml_file path and a dict of contents
    write contents to the yaml_file
    '''

    with open(yaml_file, 'w') as f:
        dump(contents, f, default_flow_style=False)

def unzip(file_path, work_dir):
    '''
    Given a file_path and a work dir
    Extract file_path to work_dir
    '''

    _file = ZipFile(file_path, 'r')
    _file.extractall(work_dir)
    _file.close()

def zip_items(output_file, items):
    '''
    Given an output_file and an iterable of items
    zip those items recursively to output_file
    '''

    call('zip -r ' + output_file + ' ' + ' '.join(items), shell=True)

def untar(file_path, work_dir):
    '''
    Given a file_path and a work_dir
    Untar file_path to work_dir
    '''

    call('tar xzf ' + file_path + ' -C ' + work_dir, shell=True)

def tar(output_file, items):
    '''
    Given an output_file and an iterable of items
    tar those items to output_file
    '''

    call('tar czf ' + output_file + ' ' + ' '.join(items), shell=True)

def read_contents(file_path):
    '''
    Given a file_path
    open and read the file
    return the contents
    '''

    with open(file_path, 'r') as f:
        return f.read()

def write_contents(file_path, contents):
    '''
    Given a file_path and some string contents
    Open the file at file_path and write contents
    this replaces existing contents
    '''

    with open(file_path, 'w') as f:
        f.write(contents)

def cleanup_items(items):
    '''
    Given an iterable of items
    call `rm -rf` on the items
    '''

    call('rm -rf ' + ' '.join(items), shell=True)

def create_path(file_path):
    '''
    Given a file_path
    check to see if it exists - if it doesn't create it
    '''

    if not exists(file_path):
        makedirs(file_path)

def sha256(file_path):
    '''
    Given a file path
    calculate the sha256 of its contents
    '''
    contents = read_contents(file_path)
    return _sha256(contents).hexdigest()
