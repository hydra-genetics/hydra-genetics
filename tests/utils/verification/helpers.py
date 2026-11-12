# coding: utf-8

"""Small fixture writers shared by the verification tests."""

import os

import pysam

VCF_HEADER = """##fileformat=VCFv4.2
##fileDate={date}
##contig=<ID=chr1,length=1000000>
##INFO=<ID=DP,Number=1,Type=Integer,Description="Depth">
##INFO=<ID=CALLERS,Number=.,Type=String,Description="Callers">
##INFO=<ID=CSQ,Number=.,Type=String,Description="Consequence annotations from Ensembl VEP. Format: Allele|Consequence|SYMBOL">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##FORMAT=<ID=AF,Number=A,Type=Float,Description="Allele fraction">
##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allele depth">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t{sample}
"""


def write_vcf(directory, name, records, sample="S1_T", date="20260101"):
    """records: list of (pos, ref, alt, af, ad_alt, callers, symbol)"""
    path = os.path.join(directory, name)
    with open(path, "w") as fh:
        fh.write(VCF_HEADER.format(date=date, sample=sample))
        line = "chr1\t{pos}\t.\t{ref}\t{alt}\t50\tPASS\tDP=100;CALLERS={callers};CSQ={alt}|missense_variant|{symbol}" \
               "\tGT:AF:AD\t0/1:{af}:{ad_ref},{ad_alt}\n"
        for pos, ref, alt, af, ad_alt, callers, symbol in records:
            fh.write(line.format(pos=pos, ref=ref, alt=alt, callers=callers, symbol=symbol, af=af, ad_ref=100 - ad_alt,
                                 ad_alt=ad_alt))
    return path


def write_bam(directory, name, reads, program="bwa mem /tmp/a.fa"):
    """reads: list of (name, pos, sequence)"""
    path = os.path.join(directory, name)
    header = {"HD": {"VN": "1.6", "SO": "coordinate"}, "SQ": [{"SN": "chr1", "LN": 1000}],
              "RG": [{"ID": "rg1", "SM": "S1_T"}], "PG": [{"ID": "bwa", "PN": "bwa", "CL": program}]}
    with pysam.AlignmentFile(path, "wb", header=header) as out:
        for read_name, pos, sequence in reads:
            segment = pysam.AlignedSegment(out.header)
            segment.query_name = read_name
            segment.reference_id = 0
            segment.reference_start = pos
            segment.mapping_quality = 60
            segment.cigarstring = "{}M".format(len(sequence))
            segment.query_sequence = sequence
            segment.query_qualities = pysam.qualitystring_to_array("I" * len(sequence))
            segment.set_tag("RG", "rg1")
            out.write(segment)
    return path


def write_text(directory, name, text):
    path = os.path.join(directory, name)
    with open(path, "w") as fh:
        fh.write(text)
    return path
