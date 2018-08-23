from retile.mutate.common import mutate_metadata

def service_broker_tile(source, work_dir, label, **kwargs):
    
    mutate_metadata(work_dir, label, 'redislabs-service-broker')
    
    
    print 'hi!'