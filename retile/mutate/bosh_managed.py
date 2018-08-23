from os import getcwd, unlink, chdir
from os.path import join
from shutil import move, rmtree
from hashlib import sha256 as _sha256

from retile import files

def bosh_managed_tile(source, work_dir, label, **kwargs):
    

    metadata_file = join(work_dir, 'metadata', 'redis-enterprise.yml')
    print 'Importing ' + metadata_file
    metadata = files.import_yaml(metadata_file)
    print 'Mutating Metadata'
    mutate_metadata(metadata, label)
    export_metadata_file = join(work_dir, 'metadata', 'redis-enterprise-' + label + '.yml')
    print 'Exporting Mutated Metadata file'
    files.export_yaml(export_metadata_file, metadata)
    print 'Eradicating Old Metadata'
    unlink(metadata_file)

    ##Then open up the release, change the label of it so it doesn't overwrite the unmutated version of the release

    _release_file = source.split('.')
    _release_file.pop()
    release_filename =  '.'.join(_release_file) + '.tgz'
    release_workdir = join(work_dir, 'releases')
    release_filepath = join(release_workdir, release_filename)
    
    print 'Extracting ' + release_filename + ' to ' + release_workdir
    files.untar(release_filepath, release_workdir)

    ##Then change the service broker config file to have a different service name and ID

    print 'Mutating Service Broker Config'
    jobs_work_dir = join(release_workdir, 'jobs')
    service_broker_job_filepath = join(release_workdir, 'jobs', 'redislabs-service-broker.tgz')
    
    files.untar(service_broker_job_filepath, jobs_work_dir)

    sb_config_template_filepath = join(jobs_work_dir, 'templates', 'config.yml.erb')
    sb_config_template = files.read_contents(sb_config_template_filepath)
    sb_config_template = sb_config_template.replace('redislabs', 'redislabs-' + label)
    sb_config_template = sb_config_template.replace('6bfa3113-5257-42d3-8ee2-5f28be9335e2', _sha256(label).hexdigest())
    files.write_contents(sb_config_template_filepath, sb_config_template)

    ##Now put it all back together

    print 'Repackaging Service Broker'
    sb_job_contents = ('templates','monit','job.MF')
   
   ##Tar takes the relative filepath, in order to make sure that everything is in the right place when Ops Manager
   ##Untars the file we need to change to the workdir to run the command

   ##I'm sure there's a way to do this in code that works around it without having to 
   ##change dirs or use the shell command, but the obvious approaches weren't working

    original_context_path = getcwd()
    chdir(jobs_work_dir) 

    files.tar(service_broker_job_filepath, sb_job_contents)
    files.cleanup_items(sb_job_contents)
    sb_sha_256 = files.sha256(service_broker_job_filepath)


    print 'Mutating Release Manifest'
    release_manifest_filepath = join(release_workdir, 'release.MF')
    release_manifest = files.import_yaml(release_manifest_filepath)
    mutate_release_manifest(release_manifest, label, sb_sha_256)
    files.export_yaml(release_manifest_filepath, release_manifest)

    print 'Repackaging Release'
    chdir(release_workdir)

    release_contents = ('release.MF', 'packages', 'jobs')
    files.tar(join(release_workdir, add_label_to_filename(release_filename, label)), release_contents)
    files.cleanup_items(release_contents)
    unlink(release_filepath)

    chdir(work_dir)

    print 'Creating New Tile'
    tile_items = ('metadata', 'migrations', 'releases', 'tile-generator')
    output_file = add_label_to_filename(source, label)
    files.zip_items(output_file, tile_items)
    move(join(work_dir, output_file), join(original_context_path, output_file))



def add_label_to_filename(filename, label):
    '''
    Given a filename structured as a .pivotal filename
    append the label in the appropriate place as to not break sem versioning
    '''

    _filename = filename.split('-')
    _filename.insert(2, label)
    return '-'.join(_filename)

def mutate_release_manifest(release_manifest, label, sb_sha_256):
    '''
    Given a parsed release_manifest object from releases/release.MF (inside redis-enterprise tarball), 
    a label and sha256 for the modify service broker tarball

    modify the release manifest to have the newly modified info
    '''

    release_manifest['name'] = release_manifest['name'] + '-' + label

    for job in release_manifest['jobs']:
        if job['name'] == 'redislabs-service-broker':
            job['sha1'] = 'sha256:' + sb_sha_256 

def mutate_metadata(metadata, label):
    '''Given a parsed metadata/redis-enterprise.yml file, modify it to allow for the tile to run next to another one'''
    
    print 'Changing tile name from ' + metadata['name'] + ' to ' + metadata['name'] + '-' + label
    metadata['name'] = metadata['name'] + '-' + label

    print 'Changing label from ' + metadata['label'] + ' to ' + metadata['label'] + ' ' + label.title()
    metadata['label'] = metadata['label'] + ' ' + label.title()

    print 'Changing provides product version name from ' + metadata['provides_product_versions'][0]['name'] + ' to ' + metadata['provides_product_versions'][0]['name'] + '-' + label
    metadata['provides_product_versions'][0]['name'] = metadata['provides_product_versions'][0]['name'] + '-' + label

    print 'Mutating Release Info'
    _metadata_releases(metadata['releases'], label)
    print 'Mutating Property Blueprints'
    _metadata_property_blueprints(metadata['property_blueprints'], label)
    print 'Mutating Job Types'
    _metadata_job_types(metadata['job_types'], label)

def _metadata_releases(releases, label):
    '''
    Given a release obj from a metadata/redis-enterprise.yml file,
    update the releases filename and name to include the label in the appropriate place
    '''

    for release in releases:
        if release.get('name') == 'redis-enterprise':
            print 'Changing release name from ' + release['name'] + ' to ' + release['name'] + '-' + label
            release['name'] = release['name'] + '-' + label
            print 'Changing release file name from ' + release['file'] + ' to ' + add_label_to_filename(release['file'], label)
            release['file'] = add_label_to_filename(release['file'], label)

def _metadata_property_blueprints(pb, label):
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

def _metadata_job_types(jts, label):
    for jt in jts:
        __metadata_release(jt['templates'], label)
        __metadata_job_types_manifest(jt, label)

def __metadata_release(templates, label):
    '''
    Given a list of releases from a job type obj from a metadata/redis-enterprise.yml file
    update release from 'redis-enterprise' to 'redis-enterprise-LABEL'
    '''
    for template in templates:
        if template['release'] == 'redis-enterprise':
            template['release'] = template['release'] + '-' + label

def __metadata_job_types_manifest(jt, label):
    '''
    Given a job type object from a metadata/redis-enterprise.yml file
    update various values in the manifest depending on which job it is
    '''

    if jt['name'] in ('broker_registrar', 'broker_deregistrar'): 
        jt['manifest'] = jt['manifest'].replace('redislabs', 'redislabs-' + label)
