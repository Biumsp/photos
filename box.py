from os.path import join, isdir, isfile
from os import listdir
from photos_utilities import write, read, validate, copy
from photos_utilities import add_one_second, decorate_class, debugger, logger


class Box():
    def __init__(self, path, create=False):
        
        if create: write(path, dir=True)
        else: validate(isdir(path), f'no directory named {path}: use -c to create one')
        self.path = path

        self.labels_path = join(path, '.labels')
        if create:
            self.labels = {}
            write(self.labels_path, {}, dumps=True, override=False) 
        else:
            self.labels = read(self.labels_path, loads=True, fail_silently=True)
            if self.labels == 'failed':
                print('Creating .labels file')
                write(self.labels_path, {}, dumps=True, override=False)

        self.files = self._list_files()

    def _list_files(self):
        return [
            f for f in listdir(self.path) 
            if f != '.labels' and isfile(f)]

    def dump(self, oldfile, newfile, labels, soft_time=False):
        if newfile in self.files:
            if soft_time:
                file = add_one_second(newfile)
                return self.dump(oldfile, file, labels, soft_time) 
            return True
        
        path = join(self.path, newfile)
        copy(oldfile, path)
        self.files.append(newfile)
        self._add_labels(newfile, labels)

    def _add_labels(self, file, labels):
        for label in labels:
            if label in self.labels:
                self.labels[label].append(file)
            else:
                self.labels.update({label: [file]})

        self._write()
    
    def _write(self):
        write(self.labels_path, self.labels, dumps=True)
        
Box = decorate_class(Box, debugger(logger), dunder=True)
