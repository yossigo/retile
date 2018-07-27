from os import makedirs, unlink, chdir, getcwd
from os.path import exists, split, join, isfile
from subprocess import Popen, call
from glob import glob
from argparse import ArgumentParser
from shutil import copyfile, rmtree, move
from zipfile import ZipFile, ZIP_DEFLATED
from yaml import load, dump
from uuid import uuid4

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

    context['_input'] = args.input[0]
    context['label'] = args.label[0]

    return context

def retile(_input, label, work_dir, **kwargs):
    '''Take input, modify to add label to metadata, create output file'''

    
    _create_fpath(work_dir)
    print 'Extracting ' + _input + ' to ' + work_dir
    _unzip_file(_input, work_dir)
    metadata_file = join(work_dir, 'metadata', 'redis-enterprise.yml')
    print 'Importing ' + metadata_file
    metadata = _import_yaml_file(metadata_file)
    print 'Mutating Metadata'
    _mutate_metadata(metadata, label)
    export_metadata_file = join(work_dir, 'metadata', 'redis-enterprise-' + label + '.yml')
    print 'Exporting Mutated Metadata file'
    _export_yaml_file(export_metadata_file, metadata)
    print 'Eradicating Old Metadata'
    unlink(metadata_file)

    _release_file = _input.split('.')
    _release_file.pop()
    release_filename =  '.'.join(_release_file) + '.tgz'
    release_workdir = join(work_dir, 'releases')
    release_filepath = join(release_workdir, release_filename)
    

    print 'Extracting ' + release_filename + ' to ' + release_workdir
    _untar_file(release_filepath, release_workdir)

    print 'Mutating Release Manifest'
    release_manifest_filepath = join(release_workdir, 'release.MF')
    release_manifest = _import_yaml_file(release_manifest_filepath)
    release_manifest['name'] = release_manifest['name'] + '-' + label
    _export_yaml_file(release_manifest_filepath, release_manifest)

    print 'Mutating Service Broker Config'
    jobs_work_dir = join(release_workdir, 'jobs')
    service_broker_job_filepath = join(release_workdir, 'jobs', 'redislabs-service-broker.tgz')
    _untar_file(service_broker_job_filepath, jobs_work_dir)

    sb_config_template_filepath = join(jobs_work_dir, 'templates', 'config.yml.erb')
    sb_config_template = _read_file_contents(sb_config_template_filepath)
    sb_config_template = sb_config_template.replace('redislabs', 'redislabs-' + label)
    sb_config_template = sb_config_template.replace('6bfa3113-5257-42d3-8ee2-5f28be9335e2', str(uuid4()))
    _write_file_contents(sb_config_template_filepath, sb_config_template)

    print 'Repackaging Service Broker'
    sb_job_contents = ('templates','monit','job.MF')
   
    original_context_path = getcwd()
    chdir(jobs_work_dir)

    _tar_file(service_broker_job_filepath, sb_job_contents)
    _cleanup_working_items(sb_job_contents)

    print 'Repackaging Release'
    chdir(release_workdir)

    release_contents = ('release.MF', 'packages', 'jobs')
    _tar_file(join(release_workdir, __add_label_to_filename(release_filename, label)), release_contents)
    _cleanup_working_items(release_contents)
    unlink(release_filepath)

    chdir(work_dir)

    print 'Creating New Tile'
    tile_items = ('metadata', 'migrations', 'releases', 'tile-generator')
    output_file = __add_label_to_filename(_input, label)
    _zip_folder_contents(output_file, tile_items)
    move(join(work_dir, output_file), join(original_context_path, output_file))


    #print 'Cleaning Up'
    #rmtree(work_dir)
    

def _args():
    '''Define args here and in retile def statement'''
    cli = ArgumentParser(prog="retile",
                                  description="Takes a Redis Enterprise for PCF tile and creates a new one with an added label, thus making it different from the unmutated tile and capable of being installed side by side."
                                  )
    cli.add_argument('input', type=str, nargs=1)
    cli.add_argument('label', type=str, nargs=1)
    cli.add_argument('--work-dir', type=str, nargs=1)

    return cli.parse_args()

def _import_yaml_file(yaml_file):
    with open(yaml_file) as f:
        return load(f)

def _export_yaml_file(yaml_file, contents):
    with open(yaml_file, 'w') as f:
        dump(contents, f, default_flow_style=False)

def _unzip_file(fpath, work_dir):
    '''Extracts fpath to work_dir'''
    _file = ZipFile(fpath, 'r')
    _file.extractall(work_dir)
    _file.close()

def _zip_folder_contents(output_file, items):
    call('zip -r ' + output_file + ' ' + ' '.join(items), shell=True)

def _untar_file(fpath, work_dir):
    call('tar xzf ' + fpath + ' -C ' + work_dir, shell=True)

def _tar_file(output_file, items):
    call('tar czf ' + output_file + ' ' + ' '.join(items), shell=True)

def _read_file_contents(fpath):
    with open(fpath, 'r') as f:
        return f.read()

def _write_file_contents(fpath, contents):
    with open(fpath, 'w') as f:
        f.write(contents)

def _cleanup_working_items(working_items):
    call('rm -rf ' + ' '.join(working_items), shell=True)

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

def __traverse_file_path(filepath):
    '''
    Given a filepath, yield files in that path.
    Is recursive, will only return files.
    '''

    files = glob(join(filepath, '*'))

    for _file in files:
        if isfile(_file):
            yield _file
        else:
            for __file in __traverse_file_path(_file):
                yield __file


if __name__ == '__main__':
    retile(**setup())
