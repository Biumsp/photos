import builtins, functools, inspect, subprocess, re, os
from shutil import copyfile
from json import loads as jsonloads
from json import dumps as jsondumps
from sys import exit
from textwrap import TextWrapper


def can_fail_silently(default=False, callback=None):
    '''
    Adds the option "fail_silently" to the function:
        if fail_silently=True, any exception in the function
        will be catched and a 'failed' will be returned
    '''

    def funk_can_fail_silently(funk):

        @functools.wraps(funk)
        def wrapper_can_fail_silently(*args, fail_silently=default, **kwargs):

            try: return funk(*args, **kwargs)
            except Exception as e:
                try: 
                    return callback(*args, **kwargs)
                except: 
                    if fail_silently: return 'failed'
                    else: raise e

        return wrapper_can_fail_silently
    return funk_can_fail_silently

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
        self.step = '    '
        self.max_width = 130
        self.color = Colorcodes()

    def spaces_step(self):
        self.step = '    '
    
    def lines_step(self):
        self.step = '│   '

    def custom_step(self, step: str):
        assert isinstance(step, str), 'step must be a string'
        self.step = step

    def auto_indent(self):
        self.indent = True

    def no_indent(self):
        self.indent = False

    def up(self):
        self.level += 1
    
    def down(self):
        if self.level > 0: self.level -= 1

    def _color(self, message, color):
        # Return unchanged if color is None (logger's default)
        if not color: return message

        try:
            color = self.color.__getattribute__(color)
            reset = self.color.reset
        except AttributeError as error:
            raise error(f'color {color} is not available')
        except Exception as error:
            raise error

        return color + message + reset
    
    @can_fail_silently(default=True, callback=builtins.print)
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

        # Add coloring
        if 'color' in kwargs:
            message = self._color(message, kwargs['color'])
            del kwargs['color']
        

print = Print()

# ------------------ End Indenting print function ------------------- #

# -----------  Logging (simple conditional printing) -------------- #
class Logger():
    '''
        A basic logging system, used by the debugger decorator:
            it uses a custom print function that allows indentation
    '''
    OFF = -1
    DEBUG = 2
    INFO  = 1

    def __init__(self):
        self.state = Logger.OFF
        self.print = Print()

    def set_state_debug(self):
        self.state = Logger.DEBUG

    def set_state_info(self):
        self.state = Logger.INFO

    def set_state_off(self):
        self.state = Logger.OFF                   

    def debug(self, message: str, color=None):
        if self.state >= Logger.DEBUG:
            self.print(message, color)
    
    def info(self, message, color=None):
        if self.state >= Logger.INFO:
            self.print(message, color)


logger = Logger()


def debugger(logger, cls=__name__):
    '''
        Logs when entering in a function and when exiting
            when the level is set to debug, it also prints
            the input arguments and the return value
    '''

    def funk_debugger(funk):

        @functools.wraps(funk)
        def wrapper_debugger(*args, **kwargs):
            
            try:
                # Clean input arguments for printing -----------

                largs = [str(arg) for arg in args]
                lkwargs = {k: str(v) for k,v in kwargs.items()}

                for i, a in enumerate(largs):
                    a = a.replace('\n', '\\n')
                    largs[i] = a

                for k, v in lkwargs.items():
                    v = v[:-1] if v.endswith('\n') else v
                    lkwargs[k] = v

                largs = ", ".join(largs)

                # Logging --------------------------------------

                logger.info(f'Entering <{cls}.{funk.__name__}>', color='green')
                logger.debug(
                    'Input: {} {}'.format(
                    largs, 
                    lkwargs if lkwargs else ''
                    ), color='orange'
                )

                try: print.up()
                except: pass

                # Calling the function -------------------------

                output = funk(*args, **kwargs)

                # Cleaning the output --------------------------

                out = [str(arg) for arg in output] if output else []

                for i, a in enumerate(out):
                    a = a.replace('\n', '\\n')
                    out[i] = a

                out = ", ".join(out)

                # Logging --------------------------------------

                logger.debug(f'Output: {out}', color='orange')
                
                return output    

            finally:
                try: print.down()
                except: pass
                logger.info(f'Exiting <{cls}.{funk.__name__}>', color='green')
                
        return wrapper_debugger
    return funk_debugger


def class_debugger(cls, logger: Logger, dunder: bool=False):
    '''Applies the decorator to all methods of a class'''

    members = inspect.getmembers(
        cls, lambda x: inspect.isfunction(x) or inspect.ismethod(x))

    for name, funk in members:
        if (not name.startswith('__') and not name.endswith('__')) or dunder:
            setattr(cls, name, debugger(funk, logger, cls.__name__))

    return cls


def decorate_class(cls, decorator, dunder=False):
    '''
        Applies the decorator to all methods of a class
    '''

    members = inspect.getmembers(
        cls, lambda x: inspect.isfunction(x) or inspect.ismethod(x))

    for name, funk in members:
        if dunder or not (name.startswith('__') and name.endswith('__')):
            setattr(cls, name, decorator(funk))

    return cls


def decorate_module(module, decorator, decorate_classes=True, dunder=False):
    '''
        Applies the decorator to all functions of a module:
            if decorate_classes=True, it also decorates
            all methods of all classes of the module
    '''

    for name in dir(module):
        obj = getattr(module, name)

        if inspect.isfunction(obj):
            setattr(module, name, decorator(obj))
        elif inspect.isclass(obj) and decorate_classes:
            setattr(module, name, decorate_class(obj, decorator, dunder))

    return module

# ------------------------ End Logging ------------------------------- #


# ----------------------------- file IO  ---------------------------- #

class InvalidPath(Exception): pass
class RenameError(Exception): pass
class DeleteError(Exception): pass
class MkdirError(Exception): pass
class WriteError(Exception): pass
class ReadError(Exception): pass
class CopyError(Exception): pass


def read(path, loads=False):
    '''Read file safely'''

    try:
        with open(path, 'r') as f:
            r = f.read()
            return jsonloads(r) if loads else r
    except Exception as e:
        raise ReadError(f'unable to read file {path}')


def mkdir(path):
    '''Create directory safely'''

    # Validate input
    if os.path.isdir(path):
        raise InvalidPath(f'directory {path} already exists')

    if os.path.isfile(path):
        raise InvalidPath(f'{path} is a file, not a directory')

    # Make directory
    try: mkdir(path)
    except Exception as e: raise MkdirError(f'cannot create directory {path}')


def write(path, text, dumps=False, override=True):
    '''Write to file safely'''

    # Dump json format
    if dumps: text = jsondumps(text)

    # Validate input
    if not override and os.path.isfile(path):
        raise InvalidPath(f'file {path} already exists')

    # Write tmp file
    tmp_path = path + '.tmp' 
    try:
        with open(tmp_path, 'w') as f:
            f.write(text)
    except Exception as e: raise WriteError(f'unable to write to {tmp_path}')

    # Move tmp file to final file
    rename(tmp_path, path)


def rename(old, new):
    '''Rename files and folders safely'''

    try:
        os.rename(old, new)
    except Exception as e: RenameError(f'unable to move {old} to {new}')


def delete(file):
    ''' Delete files safely'''

    if not os.path.isfile(file):
        raise InvalidPath(f'no file named "{file}" to delete')

    try: os.remove(file)
    except Exception as e: DeleteError(f'cannot remove file {file}')


def copy(old, new):
    '''Copy files safely'''

    try: copyfile(old, new)
    except: CopyError(f'Error: cannot copy {old} to {new}')


# ------------------------- End file IO -------------------------- #


# --------------------- CLI input validation --------------------- #ù

class ValidationError(Exception): pass

def validate(condition: bool, message: str):
    if not condition: raise ValidationError(message)


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


def none(*args):
    '''No one is true'''
    return sum(bool(x) for x in args) == 0

# -------------------- End CLI input validation ------------------- #

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
    #pattern = re.sub(r'%yy%', r'(?P<syear>\d\d)', pattern)
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

match = debugger(match, logger)


def files_iter(dir):
    files = [f for f in os.listdir(dir) if os.path.isfile(f)]
    files.sort()

    paths = [os.path.join(dir, file) for file in files]

    return zip(files, paths)

