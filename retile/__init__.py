from shutil import rmtree

from retile import mutate, files

def retile(source, work_dir, **kwargs):
    '''Take input, modify to add label to metadata, create output file'''

    ##First modify the metadata file and write a new one with a new name containing the label

    print 'Creating work dir at ' + work_dir
    files.create_path(work_dir)
    print 'Extracting ' + source + ' to ' + work_dir
    files.unzip(source, work_dir)

    if 'service-broker' not in source:
        mutate.tile('redis-enterprise', source=source, work_dir=work_dir, **kwargs)
    else:
        mutate.tile('redislabs-service-broker', source=source, work_dir=work_dir, **kwargs)

    if not kwargs.get('keep_workdir'):
        print 'Cleaning Up'
        rmtree(work_dir)
