from argparse import ArgumentParser
from retile import retile


def setup():
    '''
    Munge args and return a dict of clean data to process
    '''

    args = configure()
    context = {}
    if args.work_dir is not None:
        context['work_dir'] = args.work_dir[0]
    else:
        context['work_dir'] = '/tmp/retile'

    context['source'] = args.source[0]
    context['label'] = args.label[0]

    assert context['label'].isalpha()
    ##probably add some file check something here too

    return context


def configure():
    '''Define args here and in retile def statement'''
    cli = ArgumentParser(prog="retile",
                                  description="Takes a Redis Enterprise for PCF tile and creates a new one with an added label, thus making it different from the unmutated tile and capable of being installed side by side."
                                  )
    cli.add_argument('source', type=str, nargs=1)
    cli.add_argument('label', type=str, nargs=1)
    cli.add_argument('--work-dir', type=str, nargs=1)

    return cli.parse_args()


if __name__ == '__main__':
    retile(**setup())
