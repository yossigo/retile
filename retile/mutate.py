def add_label_to_filename(filename, label):
    '''
    Given a filename structured as a .pivotal filename
    append the label in the appropriate place as to not break sem versioning
    '''

    _filename = filename.split('-')
    _filename.insert(2, label)
    return '-'.join(_filename)

def metadata(metadata, label):
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
