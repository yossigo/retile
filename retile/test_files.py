from os.path import exists, join
from hashlib import sha256

from retile import files

WORK_DIR = '/tmp/retile'
TEST_FILE = join(WORK_DIR, 'test')

def test_import_export_yaml_tar():
    data = {"pangram":'Waltz, bad nymph, for quick jigs vex.'}
    files.export_yaml(TEST_FILE, data)
    tar_file = join(WORK_DIR, 'test.tgz')
    files.tar(tar_file, (TEST_FILE,))
    output_work_dir = join(WORK_DIR, 'tar')
    files.create_path(output_work_dir)
    files.untar(tar_file, output_work_dir)
    _data = files.import_yaml(join(output_work_dir, TEST_FILE))

    assert data == _data
    


def test_write_read_contents_sha256_zip_unzip():
    
    ##Create a data file
    data = 'Waltz, bad nymph, for quick jigs vex.'
    files.write_contents(TEST_FILE, data)
    
    ##zip, unzip and read - make sure contents match above
    zip_file = join(WORK_DIR, 'test.pivotal')
    output_work_dir = join(WORK_DIR, 'zip')
    files.zip_items(zip_file, (TEST_FILE,))
    files.unzip(zip_file, output_work_dir )
    _data = files.read_contents(join(WORK_DIR, 'zip', TEST_FILE))
    assert data == _data

    _data_hashed = files.sha256(TEST_FILE)
    assert sha256(_data).hexdigest() == _data_hashed


def test_create_path():
    files.create_path(WORK_DIR)

    assert exists(WORK_DIR)

def test_cleanup_items():

    files.cleanup_items((WORK_DIR,))

    assert not exists(WORK_DIR)

def run_tests():
    test_create_path()
    test_write_read_contents_sha256_zip_unzip()
    test_import_export_yaml_tar()
    test_cleanup_items()

if __name__ == '__main__':
    run_tests()