import os, re
from biumsputils.decorators import debugger, decorate_module, Logger
from biumsputils.print_indent import Print
import biumsputils.filesIO as filesIO


logger = Logger()
print = Print()

decorate_module(filesIO, debugger(logger))


def add_one_second(name):
    if '.' in name:
        name, ext = name.split('.')
    else:
        name, ext = name, ''

    seconds = int(name[-2:])
    minutes = int(name[-4:-2])
    hours   = int(name[-6:-4])

    invalid = False
    if seconds < 59:
        seconds += 1
    elif seconds == 59:
        seconds = 0
        if minutes < 59:
            minutes += 1
        elif minutes == 59:
            minutes = 0
            hours += 1
        else:
            invalid = True
    else:
        invalid = True
    
    if hours > 24: invalid = True

    if invalid:
        print('Error: invalid time')
        exit(1)

    seconds = str(seconds)
    minutes = str(minutes)
    hours   = str(hours)

    if len(seconds) == 1: seconds = '0' + seconds
    if len(minutes) == 1: minutes = '0' + minutes
    if len(hours)   == 1: hours   = '0' + hours

    name[-2:] = seconds
    name[-4:-2] = minutes
    name[-6:-4] = hours

    return name+'.'+ext


def match(text, pattern, bool=False):

    if '.' in text:
        text, ext = text.split('.')
    else:
        text, ext = text, ''

    # Convert pattern to capturing RegEx
    pattern = re.sub(r'\(', r'\(', pattern)
    pattern = re.sub(r'\)', r'\)', pattern)
    pattern = re.sub(r'%YYYY%', r'(?P<year>\\d\\d\\d\\d)', pattern)
    pattern = re.sub(r'%MM%', r'(?P<month>\\d\\d)', pattern)
    pattern = re.sub(r'%DD%', r'(?P<day>\\d\\d)', pattern)
    pattern = re.sub(r'%hh%', r'(?P<hour>\\d\\d)', pattern)
    pattern = re.sub(r'%mm%', r'(?P<minute>\\d\\d)', pattern)
    pattern = re.sub(r'%ss%', r'(?P<second>\\d\\d)', pattern)
    pattern = re.sub(r'%n%', r'(?P<n>\\d)', pattern)
    pattern = re.sub(r'%nn%', r'(?P<n>\\d\\d)', pattern)
    pattern = re.sub(r'%nnn%', r'(?P<n>\\d\\d\\d)', pattern)

    p = re.compile(pattern)
    m = re.match(p, text)

    if  not m: return False
    elif bool: return True

    def lookup_or_default(match, string, default):
        try: return m.group(string)
        except IndexError: return default

    year   = m.group('year')
    month  = m.group('month')
    day    = m.group('day')
    hour   = lookup_or_default(m, 'hour', '00')
    minute = lookup_or_default(m, 'minute', '00')
    second = lookup_or_default(m, 'second', '00')
    n      = lookup_or_default(m, 'n', '000')

    return year+month+day+'_'+hour+minute+second+'_'+n+'.'+ext


def files_iter(dir):
    files = [f for f in os.listdir(dir) if os.path.isfile(f)]
    files.sort()

    paths = [os.path.join(dir, file) for file in files]

    return zip(files, paths)

