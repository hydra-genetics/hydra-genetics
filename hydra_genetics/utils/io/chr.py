import re

_chr_pattern = re.compile(r'^chr[XYM0-9]+$|^[XYM0-9]+$')
_nc_pattern = re.compile(r'^NC_0+\d+\.\d+$')


class ChrTranslater(object):
    def __init__(self, mapper_file):
        self.chr_to_nc = dict()
        self.nc_to_chr = dict()

        with open(mapper_file) as mapping:
            for line in mapping:
                if not line.startswith("#"):
                    columns = line.split("\t")
                    if _chr_pattern.match(columns[0]) and _nc_pattern.match(columns[1]):
                        self.chr_to_nc[columns[0]] = columns[1]
                        self.nc_to_chr[columns[1]] = columns[0]
                    elif _chr_pattern.match(columns[1]) and _nc_pattern.match(columns[0]):
                        self.chr_to_nc[columns[1]] = columns[0]
                        self.nc_to_chr[columns[0]] = columns[1]
                    else:
                        raise Exception("Unexpected column values for column 1/2: {}".format(line))

    def get_chr_value(self, nc_id):
        return self.nc_to_chr[nc_id]

    def get_nc_value(self, chr_id):
        return self.chr_to_nc[chr_id]
