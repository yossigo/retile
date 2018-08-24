from os import unlink
from os.path import join

from retile import files
from retile.mutate.common import add_label_to_filename


def mutate(slug, work_dir, label, **kwargs):

    metadata_file = join(work_dir, 'metadata', slug + '.yml')
    print 'Importing ' + metadata_file
    metadata = files.import_yaml(metadata_file)
    print 'Mutating Metadata'

    _metadata(metadata, label)

    export_metadata_file = join(work_dir, 'metadata', slug + '-' + label + '.yml')
    print 'Exporting Mutated Metadata file'
    files.export_yaml(export_metadata_file, metadata)
    print 'Eradicating Old Metadata'
    unlink(metadata_file)
    

def _metadata(metadata, label):
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
        if release.get('name') in ('redis-enterprise', 'redislabs-service-broker'):
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
        if template['release'] in ('redis-enterprise', 'redislabs-service-broker'):
            template['release'] = template['release'] + '-' + label

def __metadata_job_types_manifest(jt, label):
    '''
    Given a job type object from a metadata/redis-enterprise.yml file
    update various values in the manifest depending on which job it is
    '''

    if jt.get('name') in ('broker_registrar', 'broker_deregistrar'): 
        jt['manifest'] = jt['manifest'].replace('redislabs', 'redislabs-' + label)