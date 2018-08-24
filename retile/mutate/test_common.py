from common import add_label_to_filename

def test_add_label_to_filename():

    filename = 'foo-bar-baz'
    label = 'label'

    output = add_label_to_filename(filename, label)
    assert output == 'foo-bar-label-baz'

    filename = 'foo-service-broker'
    output = add_label_to_filename(filename, label)
    assert output == 'foo-service-broker-label'


def run_tests():

    test_add_label_to_filename()

if __name__ == '__main__':
    run_tests()