# vim: syntax=python tabstop=4 expandtab
# coding: utf-8

from enum import Enum, auto, unique
import enum
import re

import pysam

_cds_pattern = re.compile(r'^c\..+|^-$')
_aa_pattern = re.compile(r'^p\..+|^-$')
_exon_intron_pattern = re.compile(r'^exon\d+$|^intronic$')
_chr_pattern = re.compile(r'^chr[XYM0-9]+$|^[XYM0-9]+$')
_nc_pattern = re.compile(r'^NC_0+\d+\.\d+$')


def is_indel(variant):
    if len(variant.alleles) != 2:
        raise Exception("Unhandled case: " + str(variant.alleles))
    return (len(variant.alleles[0]) == 1 and len(variant.alleles[1]) > 1) or \
           (len(variant.alleles[1]) == 1 and len(variant.alleles[0]) > 1)


@unique
class VariantClass(Enum):
    hotspot = 1
    indel = 2
    check = 3
    other = 4

    def __str__(self):
        return '%s-%s' % (self.value, self.name)


@unique
class ReportClass(Enum):
    hotspot = auto()
    indel = auto()
    region = auto()
    region_all = auto()

    def __str__(self):
        return '%s' % self.name


class MultiBpVariant(object):
    def __init__(self, CHROMOSOME, START, STOP, REFERENCE, VARIANT, GENE, CDS_CHANGE, AA_CHANGE, TRANSCRIPT):
        self.CHROMOSOME = CHROMOSOME
        self.START = START
        self.STOP = STOP
        self.REFERENCE = REFERENCE
        self.VARIANT = VARIANT
        self.GENE = GENE
        self.CDS_CHANGE = CDS_CHANGE
        self.AA_CHANGE = AA_CHANGE
        self.TRANSCRIPT = TRANSCRIPT.split(".")[0]

    def __str__(self):
        return "{}\t{}\t{}\t{}\t{}".format(self.CHROMOSOME, self.START, self.STOP, self.REFERENCE, self.VARIANT)


class MultiBpVariantData(object):
    def __init__(self, data_file):
        self.data = {}
        from hydra_genetics.utils.io.multibp import Reader
        reader = Reader(data_file)
        for bp in reader:
            key = "{}:{}:{}:{}:{}".format(bp.CHROMOSOME, bp.START, bp.STOP, bp.REFERENCE, bp.VARIANT)
            if key in self.data:
                raise Exception("Trying to overwrite data for: " + key)

            self.data[key] = bp

    def get_data(self, chromosome, start, stop, reference, variant):
        return self.data.get("{}:{}:{}:{}:{}".format(chromosome, start, stop, reference, variant), None)


class Hotspot(object):
    def __init__(self, CHROMOSOME, START, END, GENE, CDS_MUTATION_SYNTAX, AA_MUTATION_SYNTAX, REPORT, COMMENT,
                 EXON, ACCESSION_NUMBER, ALWAYS_PRINT=False, PRINT_ALL=False):
        self.CHROMOSOME = CHROMOSOME
        self.CHR_SHORT = "chr" + re.sub(r'^NC_[0]*|\.[0-9]*$', '', CHROMOSOME)
        self.START = START
        self.END = END
        self.GENE = GENE
        self.CDS_MUTATION_SYNTAX = CDS_MUTATION_SYNTAX
        self.AA_MUTATION_SYNTAX = AA_MUTATION_SYNTAX
        self.REPORT = REPORT
        self.COMMENT = COMMENT
        self.EXON = EXON
        self.ACCESSION_NUMBER = ACCESSION_NUMBER
        self.ALWAYS_PRINT = ALWAYS_PRINT

        if not isinstance(self.START, int):
            raise ValueError("Start position should be an integer: %s!" % self.START)

        if not isinstance(self.END, int):
            raise ValueError("End position should be an integer: %s!" % self.END)

        if self.START > self.END:
            raise ValueError("Start cordinte cannot be larget then stop coordinate! start:%s > stop:%s" %
                             (self.START, self.END))

        if not _cds_pattern.match(self.CDS_MUTATION_SYNTAX):
            raise ValueError("Incorrect cds syntax %s! Should start with \"c.\" or set to \"-\" if empty." %
                             self.CDS_MUTATION_SYNTAX)

        if not _aa_pattern.match(self.AA_MUTATION_SYNTAX):
            raise ValueError("Incorrect aa syntax: %s! Should start with \"p.\" or set to \"-\" if empty." %
                             self.AA_MUTATION_SYNTAX)

        if self.REPORT in ReportClass.__members__:
            raise ValueError("report value (%s) not found in  Enum class %s!" % (self.REPORT, list(ReportClass)))

        if not _exon_intron_pattern.match(self.EXON):
            raise ValueError("Exon value should have the following format: exon or intronic. not %" % self.EXON)

        self.VARIANTS = [{'extended': False, 'variants': []} for i in range((self.END - self.START + 1))]

        self.EXTENDED_START = self.START
        self.EXTENDED_END = self.END
        self.PRINT_ALL = PRINT_ALL
        self.VARIANT_ADDED = False

    def check_overlapp(self, chrom, region_start, region_stop, start, stop=None):
        return self.CHROMOSOME == chrom and \
               ((stop is not None and region_start <= stop and start <= region_stop) or (region_start <= start <= region_stop))

    def add_variant(self, variant, chr_translater):
        if isinstance(variant, pysam.VariantRecord):
            if len(variant.ref) == 1 and len(variant.alts[0]) == 1 and self.REPORT == ReportClass.indel:
                return False
            v_start = variant.start + 1
            v_stop = variant.stop + 1

            if self.check_overlapp(chr_translater.get_nc_value(variant.chrom), self.START, self.END, v_start, v_stop):
                if self.REPORT == ReportClass.indel and not is_indel(variant):
                    return False
                if self.EXTENDED_END < v_stop or v_start < self.EXTENDED_START:
                    if variant.start < self.EXTENDED_START or self.EXTENDED_END < variant.stop:
                        new_start = min(v_start, self.EXTENDED_START)
                        new_end = max(v_stop, self.EXTENDED_END)
                        new_var = []
                        for i in range(new_end - new_start + 1):
                            if self.START <= i + new_start <= self.END:
                                new_var.append(self.VARIANTS[new_start - self.EXTENDED_START + i])
                            else:
                                new_var.append({'extended': True, 'variants': []})
                        self.VARIANTS = new_var
                        self.EXTENDED_START = new_start
                        self.EXTENDED_END = new_end
                position = v_start - self.EXTENDED_START
                # try:
                self.VARIANTS[position]['variants'].append(variant)
                # except:
                #    self.DEPTH_VARIANTS[position]['variants'] = [variant]
                self.VARIANT_ADDED = True
                return True
        return False

    def __str__(self):
        return self.CHROMOSOME + ":" + str(self.START) + "-" + str(self.END) + " " + str(self.REPORT)
