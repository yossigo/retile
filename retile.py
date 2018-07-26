from os import makedirs
from os.path import exists, split, join
from argparse import ArgumentParser
from shutil import copyfile
from zipfile import ZipFile
from yaml import load

def setup():
    '''
    Munge args and return a dict of clean data to process
    '''

    args = _args()
    context = {}
    if args.work_dir is not None:
        context['work_dir'] = args.work_dir[0]
    else:
        context['work_dir'] = '/tmp/retile'

    context['input'] = args.input[0]
    context['output'] = args.output[0]
    context['label'] = args.label[0]

    return context

def retile(input, output, label, work_dir, **kwargs):
    '''Take input, modify to add label to metadata, create output file'''

    _create_fpath(work_dir)
    _unzip_file(input, work_dir)
    print 'Importing ' + join(work_dir, 'metadata', 'redis-enterprise.yml')
    metadata = _import_yaml_file(join(work_dir, 'metadata', 'redis-enterprise.yml'))
    mutated_metadata = _mutate_metadata(metadata, label)
    

def _args():
    '''Define args here and in retile def statement'''
    cli = ArgumentParser(prog="retile",
                                  description="Takes a Redis Enterprise for PCF tile and creates a new one with an added label, thus making it different from the unmutated tile and capable of being installed side by side."
                                  )
    cli.add_argument('input', type=str, nargs=1)
    cli.add_argument('output', type=str, nargs=1)
    cli.add_argument('label', type=str, nargs=1)
    cli.add_argument('--work-dir', type=str, nargs=1)

    return cli.parse_args()


# def _move_file_to_folder(fpath, folder):
#     '''Given a filepath and destination folder, move the filepath to the folder'''
    
#     root, file_name = split(fpath)
#     dest = join(folder, file_name)
    
#     print 'Moving ' + fpath + ' to ' + dest
    
#     copyfile(fpath, dest)

def _import_yaml_file(yaml_file):

    with open(yaml_file) as f:
        return load(f)


def _unzip_file(fpath, work_dir):
    '''Extracts fpath to work_dir'''
    print 'Extracting ' + fpath + ' to ' + work_dir
    _file = ZipFile(fpath, 'r')
    _file.extractall(work_dir)
    _file.close()


def _create_fpath(fpath):
    '''Given a file path, check to see if it exists - if it doesn't create it'''
    if not exists(fpath):
        print 'Creating ' + fpath
        makedirs(fpath)

def _mutate_metadata(metadata, label):
    '''Given a parsed metadata/redis-enterprise.yml file, modify it to allow for the tile to run next to another one'''
    
    print 'Changing tile name from ' + metadata['name'] + ' to ' + metadata['name'] + '-' + label
    metadata['name'] = metadata['name'] + '-' + label

    print 'Changing label from ' + metadata['label'] + ' to ' + metadata['label'] + ' ' + label.title()
    metadata['label'] = metadata['label'] + ' ' + label.title()

    print 'Changing provides product version name from ' + metadata['provides_product_versions'][0]['name'] + ' to ' + metadata['provides_product_versions'][0]['name'] + '-' + label
    metadata['provides_product_versions'][0]['name'] = metadata['provides_product_versions'][0]['name'] + '-' + label

    print 'Mutating Release Info'
    __mutate_releases(metadata['releases'], label)
    print 'Mutating Property Blueprints'
    __mutate_property_blueprints(metadata['property_blueprints'], label)
    print 'Mutating Job Types'
    __mutate_job_types(metadata['job_types'], label)

    # print metadata['name']
    # print metadata['label']
    # print metadata['releases']
    # print metadata['provides_product_versions']
    # print metadata['property_blueprints']
    # print metadata['job_types']
    # import pdb; pdb.set_trace()

    # print metadata.keys()

    return None


def __mutate_releases(releases, label):
    '''
    Given a release obj from a metadata/redis-enterprise.yml file,
    update the releases filename and name to include the label in the appropriate place
    '''

    for release in releases:
        if release.get('name') == 'redis-enterprise':
            print 'Changing release name from ' + release['name'] + ' to ' + release['name'] + '-' + label
            release['name'] = release['name'] + '-' + label
            print 'Changing release file name from ' + release['file'] + ' to ' + __add_label_to_filename(release['file'], label)
            release['file'] = __add_label_to_filename(release['file'], label)

def __mutate_property_blueprints(pb, label):
    '''
    Given a property blueprints obj from a metadata/redis-enterprise.yml file
    update property defaults that would clash with other installs by adding a . or - and the label
    depending on what the property is
    '''

    props_to_mutate = ('org', 'space', 'redis_broker_domain', 'redis_api_domain', 'redis_console_domain')
    for prop in pb:
        if prop['name'] in props_to_mutate:
            # dots vs dashes
            if 'domain' in prop['name']:
                domain_name = prop['default'].split('.')
                domain_name[0] = domain_name[0] + '-' + label
                prop['default'] = '.'.join(domain_name)
            else:
                name = prop['default'].split('-')
                name.insert(2, label)
                prop['default'] = '-'.join(name)

def __mutate_job_types(jts, label):
    for jt in jts:
        __mutate_release_in_templates(jt['templates'], label)
        __mutate_manifest_in_job_type(jt, label)
        # print jt['templates']

def __mutate_release_in_templates(templates, label):
    '''
    Given a list of releases from a job type obj from a metadata/redis-enterprise.yml file
    update release from 'redis-enterprise' to 'redis-enterprise-LABEL'
    '''
    for template in templates:
        if template['release'] == 'redis-enterprise':
            template['release'] = template['release'] + '-' + label

def __mutate_manifest_in_job_type(jt, label):
    '''
    Given a job type object from a metadata/redis-enterprise.yml file
    update various values in the manifest depending on which job it is
    '''

    if jt['name'] in ('broker_registrar', 'broker_deregistrar'): 
        jt['manifest'] = jt['manifest'].replace('redislabs', 'redislabs-' + label)

def __add_label_to_filename(filename, label):
    '''
    Given a filename structured as a .pivotal filename
    append the label in the appropriate place as to not break sem versioning
    '''

    _filename = filename.split('-')
    _filename.insert(2, label)
    return '-'.join(_filename)



if __name__ == '__main__':
    retile(**setup())
