def add_label_to_filename(filename, label):
    '''
    Given a filename structured as a .pivotal filename
    append the label in the appropriate place as to not break sem versioning
    '''
    
    if 'broker' in filename:
        shim = 3
    else:
        shim = 2

    _filename = filename.split('-')
    _filename.insert(shim, label)
    return '-'.join(_filename)
