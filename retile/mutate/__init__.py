from os import getcwd
from os.path import join, basename
from shutil import move

from retile import files
from retile.mutate import release, metadata
from retile.mutate.common import add_label_to_filename

def tile(slug, **kwargs):
    original_context_path = getcwd()

    metadata.mutate(slug, **kwargs)
    release.mutate(**kwargs)

    _rebuild_tile(original_context_path, **kwargs)

def _rebuild_tile(original_context_path, source, work_dir, label, **kwargs):
    print 'Creating New Tile'
    tile_items = ('metadata', 'migrations', 'releases', 'tile-generator')
    output_file = add_label_to_filename(basename(source), label)
    files.zip_items(output_file, tile_items)
    move(join(work_dir, output_file), join(original_context_path, output_file))
