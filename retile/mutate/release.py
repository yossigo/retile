from os import getcwd, chdir, unlink
from os.path import join
from hashlib import sha256

from retile import files
from retile.mutate.common import add_label_to_filename

def mutate(source, work_dir, label, **kwargs):

    _release_file = source.split('.')
    _release_file.pop()
    release_filename =  '.'.join(_release_file) + '.tgz'

    release_work_dir = join(work_dir, 'releases')
    release_filepath = join(release_work_dir, release_filename)
    files.untar(release_filepath, release_work_dir)
    
    jobs_work_dir = join(release_work_dir, 'jobs')
    service_broker_job_filepath = join(jobs_work_dir,'redislabs-service-broker.tgz')

    _mutate_service_broker_config(jobs_work_dir, service_broker_job_filepath, label)
    sha = _repackage_service_broker(jobs_work_dir, service_broker_job_filepath)
    _mutate_release_manifest(release_work_dir, sha, label)
    _repackage_release(work_dir, release_work_dir, release_filename, release_filepath, label)


def _mutate_service_broker_config(jobs_work_dir, service_broker_job_filepath, label):
    ##Then change the service broker config file to have a different service name and ID
    
    print 'Mutating Service Broker Config'
    files.untar(service_broker_job_filepath, jobs_work_dir)

    sb_config_template_filepath = join(jobs_work_dir, 'templates', 'config.yml.erb')
    sb_config_template = files.read_contents(sb_config_template_filepath)
    sb_config_template = sb_config_template.replace('redislabs', 'redislabs-' + label)
    sb_config_template = sb_config_template.replace('6bfa3113-5257-42d3-8ee2-5f28be9335e2', sha256(label).hexdigest())
    files.write_contents(sb_config_template_filepath, sb_config_template)

def _repackage_service_broker(jobs_work_dir, service_broker_job_filepath):
    ##Now put it all back together

    print 'Repackaging Service Broker'
    sb_job_contents = ('templates','monit','job.MF')

    ##Tar takes the relative filepath, in order to make sure that everything is in the right place when Ops Manager
    ##Untars the file we need to change to the workdir to run the command

    ##I'm sure there's a way to do this in code that works around it without having to 
    ##change dirs or use the shell command, but the obvious approaches weren't working

    chdir(jobs_work_dir) 

    files.tar(service_broker_job_filepath, sb_job_contents)
    files.cleanup_items(sb_job_contents)
    return files.sha256(service_broker_job_filepath)

def _mutate_release_manifest(release_work_dir, sb_sha_256, label):

    print 'Mutating Release Manifest'
    release_manifest_filepath = join(release_work_dir, 'release.MF')
    release_manifest = files.import_yaml(release_manifest_filepath)

    # '''
    # Given a parsed release_manifest object from releases/release.MF (inside redis-enterprise tarball), 
    # a label and sha256 for the modify service broker tarball

    # modify the release manifest to have the newly modified info
    # '''
    release_manifest['name'] = release_manifest['name'] + '-' + label

    for job in release_manifest['jobs']:
        if job['name'] == 'redislabs-service-broker':
            job['sha1'] = 'sha256:' + sb_sha_256 

    files.export_yaml(release_manifest_filepath, release_manifest)

def _repackage_release(work_dir, release_work_dir, release_filename, release_filepath, label):
    print 'Repackaging Release'
    chdir(release_work_dir)

    release_contents = ('release.MF', 'packages', 'jobs')
    files.tar(join(release_work_dir, add_label_to_filename(release_filename, label)), release_contents)
    files.cleanup_items(release_contents)
    unlink(release_filepath)

    chdir(work_dir)
