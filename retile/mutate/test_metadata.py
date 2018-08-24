import metadata

def test__metadata():
    _metadata = {'name':'name',
                'label':'label',
                'provides_product_versions':[{'name':'name'}],
                'releases':[],
                'property_blueprints':[],
                'job_types':[]}
    metadata._metadata(_metadata, 'label')

    assert _metadata['name'] == 'name-label'
    assert _metadata['provides_product_versions'][0]['name'] == 'name-label'
    assert _metadata['label'] == 'label Label'

def test__metadata_releases():
    releases = [{'name':'redis-enterprise', 'file':'foo-bar-baz-3243151.23431.31143.pivotal'},
                {'name':'not-redis-enterprise'}]
    metadata._metadata_releases(releases, 'label')

    assert releases[0]['file'] == 'foo-bar-label-baz-3243151.23431.31143.pivotal'
    assert releases[0]['name'] == 'redis-enterprise-label'
    assert releases[1] == {'name':'not-redis-enterprise'}

def test__metadata_property_blueprints():
    property_blueprints = [{'name':'org', 'default':'foo-bar-baz'},
                           {'name':'redis_api_domain', 'default':'foo.bar.baz'},
                           {'name':'not-relevant-to-us'}]
    metadata._metadata_property_blueprints(property_blueprints, 'label')
    
    assert property_blueprints[0]['default'] == 'foo-bar-label-baz'
    assert property_blueprints[1]['default'] == 'foo-label.bar.baz'
    assert property_blueprints[2] == {'name':'not-relevant-to-us'}


def test___metadata_release():
    templates = [{'release':'redis-enterprise'}, {'release':'not-redis-enterprise'}]
    label = 'label'

    metadata.__metadata_release(templates, label)

    assert templates[0]['release'] == 'redis-enterprise-label'
    assert templates[1]['release'] == 'not-redis-enterprise'


def test___metadata_job_types_manifest():
    label = 'label'

    jt = {'name':'broker_registrar', 'manifest':'redislabs'}
    metadata.__metadata_job_types_manifest(jt, label)
    assert jt['manifest'] == 'redislabs-label'

    jt = {'name':'broker_deregistrar', 'manifest':'redislabs'}
    metadata.__metadata_job_types_manifest(jt, label)
    assert jt['manifest'] == 'redislabs-label'

    jt = {'name':'nothing-todo-with-us'}
    _jt = jt.copy()
    metadata.__metadata_job_types_manifest(jt, label)
    assert jt == _jt

    jt = {}
    metadata.__metadata_job_types_manifest(jt, label)
    assert jt == {}

def run_tests():
    test___metadata_job_types_manifest()
    test___metadata_release()
    test__metadata_property_blueprints()
    test__metadata_releases()
    test__metadata()

if __name__ == '__main__':
    run_tests()