from utilities import print, read, write, delete
from utilities import requires, excludes, check
from utilities import match
from utilities import logger
from box import Box
import os, click

# Read configurations
HOME = os.path.expanduser('~')
CONFIG = os.path.join(HOME, '.config/photos/photos_config.json') 

CONFIG = read(CONFIG, loads=True)
PATTERNS = CONFIG['patterns']   # {"pattern": "source"}
LABELS = CONFIG['labels']       # {"source" : ["labels"]}
NO_TIME_SOURCES = CONFIG['no_time_sources'] # ["sources"]

@click.group(no_args_is_help=True)
@click.option('--logging-info', is_flag=True, help='Set logging to info')
@click.option('--logging-debug', is_flag=True, help='Set logging to debug')
@click.option('--indent', is_flag=True, help='Nested indentation')
def cli(logging_info, logging_debug, indent):

    # Validate input
    check(excludes(logging_debug, logging_info), 'can only set one info level')

    # Set logging state
    if logging_debug: state = logger.DEBUG 
    elif logging_info: state = logger.INFO 
    else: state = logger.OFF

    logger.set_state(state)

    print.set_indent(indent)


@cli.command(no_args_is_help=True)
@click.argument('folder', type=click.Path(), required=True)
@click.option('--box', '-b', default=None, type=click.Path(), help='Add to a box storage: path to box')
@click.option('--create', '-c', is_flag=True, help='Create new box storage')
@click.option('--labels / --no-labels', default=True, is_flag=True, help='Label using box')
@click.option(
    '--delete', '-D', 'delete', count=True,
    help='D: Delete once renamed\nDD: delete once moved into the box')
def format(folder, box, create, labels, delete):

    # Validate input
    check(os.path.isdir(folder), 'folder is invalid')
    check(requires(create, box), '--create requires --box')
    check(requires(delete, box), '--delete requires --box')
    check(delete < 3, '--delete (-D) has a max of 2 (-DD)')

    if box: box = Box(box, create)  
    skipped = []    # All (skipped file, reason) pairs

    # Create the folder for renamed files
    renamed_folder = os.path.join(folder, "renamed")
    write(renamed_folder, dir=True, soft=True)

    # Rename each file (and optionally box them)
    files = os.listdir(folder)
    files.sort()
    for file in files:

        filename = os.path.join(folder, file)
        if os.path.isfile(filename):

            sources = set()
            for pattern in PATTERNS:
                if match(filename, pattern, bool=True):
                    sources.add(PATTERNS[pattern])
                    
                    newname = match(filename, pattern)
                    renamed = os.path.join(renamed_folder, newname)
                    
            # If only one source matched
            if len(sources) == 1:
                
                source = list(sources)[0]
                soft_time = source in NO_TIME_SOURCES

                # Returns true if fails
                if write(newname, override=False, soft=True):
                    skipped.append((filename, 'conflict in "rename" folder'))
                    continue

                if box:
                    labels = LABELS[source] if labels else []

                    # Returns true if fails 
                    failed = box.dump(renamed, newname, labels, soft_time=soft_time)
                    if failed:
                        skipped.append((filename, 'conflict in the box'))
                    continue

            elif len(sources) == 0:
                skipped.append((filename, "no matches"))
                continue
                
            else:
                skipped.append((filename, "ambiguous match"))
                continue

        if delete > 0: delete(filename)
        if delete > 1: delete(renamed)


    skipped.sort(key=lambda x: x[1])
    for file, reason in skipped:
        print(f'file {file} skipped: {reason}')
