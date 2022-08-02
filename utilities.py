import builtins, functools, inspect, subprocess
from shutil import copyfile
from json import loads as jsonloads
from json import dumps as jsondumps
from sys import exit
from os import rename, remove, path, mkdir
from textwrap import TextWrapper

from sympy import sec

# -------------------------- Colorcodes ---------------------------- #
class Colorcodes(object):
    """
    Provides ANSI terminal color codes which are gathered via the ``tput``
    utility. That way, they are portable. If there occurs any error with
    ``tput``, all codes are initialized as an empty string.
    The provides fields are listed below.
    Control:
    - bold
    - reset
    Colors:
    - blue
    - green
    - orange
    - red
    :license: MIT
    """
    def __init__(self):
        try:
            self.bold = subprocess.check_output("tput bold".split()).decode("utf-8")
            self.reset = subprocess.check_output("tput sgr0".split()).decode("utf-8")

            self.blue = subprocess.check_output("tput setaf 4".split()).decode("utf-8")
            self.green = subprocess.check_output("tput setaf 2".split()).decode("utf-8")
            self.orange = subprocess.check_output("tput setaf 3".split()).decode("utf-8")
            self.red = subprocess.check_output("tput setaf 1".split()).decode("utf-8")

        except subprocess.CalledProcessError as e:
            self.bold = ""
            self.reset = ""

            self.blue = ""
            self.green = ""
            self.orange = ""
            self.red = ""

# ------------------------ End Colorcodes -------------------------- #

# -------------------- Indenting print function -------------------- #
class Print():
    '''
        print function that auto-indents before 
        printing, with custom indent and max width. 
        By default it behaves like the builtin print().
        It also enables color coding.
    '''

    def __init__(self):
        self.level = 0
        self.indent = False
        self.step = '    ' # '│   '
        self.max_width = 80
        self.color = Colorcodes()

    def set_indent(self, indent):
        self.indent = indent

    def up(self):
        self.level += 1
    
    def down(self):
        if self.level > 0: self.level -= 1

    def _color(self, message, color):
        if not self.color: return message

        try:
            color = self.color.__getattribute__(color)
        except AttributeError:
            print(f'Error: color {color} is not available')
            exit(1)

        reset = self.color.reset

        return color + message + reset
    
    def __call__(self, *args, **kwargs):

        sep = kwargs['sep'] if 'sep' in kwargs else ' '
        message = sep.join(args)

        if self.indent:
            wrapper = TextWrapper(
                initial_indent=self.step*self.level,
                subsequent_indent=self.step*self.level + '├─',
                width=self.max_width)

            message = wrapper.fill(message)

            # Replace the last "new-line" symbol
            message = message[::-1].replace('─├', '─└',1)[::-1]

        # Manage colors
        if 'color' in kwargs:
            message = self._color(message, kwargs['color'])
            del kwargs['color']

        builtins.print(message, **kwargs)

print = Print()

# ------------------ End Indenting print function ------------------- #


# ----------------------------- file IO  ---------------------------- #
def read(path, loads=False):

    try:
        with open(path, 'r') as f:
            r = f.read()
            return jsonloads(r) if loads else r
    except:
        print(f'Error: unable to read file {path}')
        exit(1)


def write(path, text, dumps=False, override=True, dir=False, soft=False):

    if not override:
        if not dir and path.isfile(path):
            if soft: return
            print(f'Error: file {path} already exists')
            return True

        elif dir and path.isdir(path):
            if soft: return
            print(f'Error: directory {path} already exists')
            return True

        elif dir and path.isfile(path):
            print(f'Error: {path} is a file, not a directory')
            exit(1)

    if dir:
        try: mkdir(path)
        except:
            print(f'Error: cannot create directory {path}')
            exit(1)           

    tmp_path = path + '.tmp'
    if dumps: text = jsondumps(text) 

    try:
        with open(tmp_path, 'w') as f:
            f.write(text)
    except:
        print(f'Error: unable to write to {tmp_path}') 
        exit(1)       

    try:
        rename(tmp_path, path)
    except:
        print(f'Error: unable to move {tmp_path} to {path}')
        exit(1)


def delete(file, soft=True):
    '''
        The soft option returns instead of crushing
        when the file does not exist
    '''

    try:
        if soft and not path.isfile(file):
            return 
        remove(file)
    except Exception as e:
        print(f'Error: cannot remove file {file} due to "{e}"')
        exit(1)


def copy(old, new):
    try: copyfile(old, new)
    except:
        print(f'Error: cannot copy {old} to {new}')
        exit(1)

# ------------------------- End file IO -------------------------- #


# --------------------- CLI input validation --------------------- #
def requires(arg, *args):
    '''If you have arg, you need at least one of the args'''

    if not bool(arg):
        return True
    
    return any(bool(a) for a in args)


def excludes(arg, *args):
    '''If you have arg, you cannot have ant of the args'''

    if not bool(arg):
        return True

    return none(*args)


def check(condition: bool, error: str):
    if not condition:
        print('Error: ' + error)
        exit(1)


def none(*args):
    '''No one is true'''
    return sum(bool(x) for x in args) == 0

# -------------------- End CLI input validation ------------------- #


# -----------  Logging (simple conditional printing) -------------- #
class Logger():
    OFF = -1
    DEBUG = 2
    INFO  = 1

    def __init__(self):
        self.state = Logger.OFF

    def set_state(self, state):
        self.state = state

    def debug(self, message):
        if self.state >= Logger.DEBUG:
            print(message)
    
    def info(self, message):
        if self.state >= Logger.INFO:
            print(message)


logger = Logger()


def debugger(funk, logger, cls):
    '''Logs when entering in a function and when exiting'''

    @functools.wraps(funk)
    def wrapper_debugger(*args, **kwargs):
        
        try:
            largs = [str(arg) for arg in args]
            lkwargs = {(k, str(v)) for k,v in kwargs.items()}

            for i, a in enumerate(largs):
                a = a.replace('\n', '\\n')
                largs[i] = a

            for k, v in lkwargs:
                v = v[:-1] if v.endswith('\n') else v
                lkwargs[k] = v

            largs = ", ".join(largs)

            logger.debug('Entering <{}.{}>'.format(
                cls,
                funk.__name__
            ))

            logger.debug('Parameters: {} {}'.format(
                largs, 
                lkwargs if lkwargs else ''
            ))

            logger.info(f'Entering <{cls}.{funk.__name__}>')

            return funk(*args, **kwargs)    

        finally:
            logger.info(f'Exiting <{cls}.{funk.__name__}>')

    return wrapper_debugger


def class_debugger(cls, logger):
    '''Applies the decorator to all methods of a class'''
    members = inspect.getmembers(
        cls, lambda x: inspect.isfunction(x) or inspect.ismethod(x))

    for name, funk in members:
        if not name.startswith('__') and not name.endswith('__'):
            setattr(cls, name, debugger(funk, logger, cls.__name__))

    return cls

# ------------------------ End Logging ------------------------------- #

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

    return name
