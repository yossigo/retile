from os import getcwd, unlink, chdir
from os.path import join
from shutil import move, rmtree
from uuid import uuid4

from retile import mutate, files

def retile(source, label, work_dir, **kwargs):
    '''Take input, modify to add label to metadata, create output file'''

    ##First modify the metadata file and write a new one with a new name containing the label

    print 'Creating work dir at ' + work_dir
    files.create_path(work_dir)
    print 'Extracting ' + source + ' to ' + work_dir
    files.unzip(source, work_dir)
    metadata_file = join(work_dir, 'metadata', 'redis-enterprise.yml')
    print 'Importing ' + metadata_file
    metadata = files.import_yaml(metadata_file)
    print 'Mutating Metadata'
    mutate.metadata(metadata, label)
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
    sb_config_template = sb_config_template.replace('6bfa3113-5257-42d3-8ee2-5f28be9335e2', str(uuid4()))
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
    mutate.release_manifest(release_manifest, label, sb_sha_256)
    files.export_yaml(release_manifest_filepath, release_manifest)

    print 'Repackaging Release'
    chdir(release_workdir)

    release_contents = ('release.MF', 'packages', 'jobs')
    files.tar(join(release_workdir, mutate.add_label_to_filename(release_filename, label)), release_contents)
    files.cleanup_items(release_contents)
    unlink(release_filepath)

    chdir(work_dir)

    print 'Creating New Tile'
    tile_items = ('metadata', 'migrations', 'releases', 'tile-generator')
    output_file = mutate.add_label_to_filename(source, label)
    files.zip_items(output_file, tile_items)
    move(join(work_dir, output_file), join(original_context_path, output_file))


    print 'Cleaning Up'
    rmtree(work_dir)