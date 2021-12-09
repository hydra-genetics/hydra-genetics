# vim: syntax=python tabstop=4 expandtab
# coding: utf-8

import re

from hydra_genetics.utils.models.hotspot import MultiBpVariant


class Reader(object):
    def __init__(self, filename, compressed=None, encoding='ascii'):
        super().__init__()

        if not filename:
            raise Exception("A filepath needs to be specified: %" % filepath)

        if compressed:
            self._reader = codecs.getreader(encoding)(self._reader)
        else:
            if compressed is None:
                compressed = filename.endswith('.gz')
        self._reader = open(filename, 'rb' if compressed else 'rt')
        self.filename = filename

        self.reader = (line.rstrip() for line in self._reader)

        self._row_pattern = re.compile("\t")

    def __del__(self):
        if self._reader and not self._reader.closed:
            self._reader.close()

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        '''Return the next record in the file.'''
        line = next(self.reader)
        row = self._row_pattern.split(line.rstrip())
        chrom = row[0]
        start = row[1]
        stop = row[2]
        ref = row[3]
        var = row[4]
        gene = row[5]
        cds_change = row[6]
        aa_change = row[7]
        transcript = row[8]

        return MultiBpVariant(chrom, start, stop, ref, var, gene, cds_change, aa_change, transcript)
