import pysam
from pysam import VariantFile
import statistics
import warnings

from hydra_genetics.utils.models.hotspot import ReportClass


def add_contigs_to_header(input_name, output_name, contig_file, assembly):
    from src.lib.data.files.reference import InfoImporter
    info = InfoImporter(contig_file)
    input_vcf = VariantFile(input_name, 'r')
    for key in info:
        input_vcf.header.contigs.add(key, length=info[key]['length'], assembly=assembly)
    output_vcf = VariantFile(output_name, 'w', header=input_vcf.header)
    for record in input_vcf:
        output_vcf.write(record)


def get_annotation_data(data_extracter, mapper):
    return lambda variant, field: data_extracter(variant, mapper[field])


def get_annoation_data_vep(field_dict):
    def extractor(variant, info_name):
        if isinstance(variant, pysam.VariantRecord):
            try:
                data = variant.info['CSQ'][0].split("|")[field_dict[info_name]]
                if data is None:
                    return "-"
                if isinstance(data, tuple):
                    return ",".join(data)
                return data
            except KeyError:
                return "-"
        return "-"
    return extractor


def get_depth(gvcf_file, sample, chr, start, stop):
    depth = [r.samples[sample]['DP'] for r in gvcf_file.fetch(chr, start, stop)]
    if len(depth) > 1:
        return statistics.mean(depth)
    elif len(depth) == 1:
        return depth[0]
    else:
        return 0


def get_info_field(variant, info_name):
    if isinstance(variant, pysam.VariantRecord):
        try:
            data = variant.info[info_name]
            if data is None:
                return "-"
            if isinstance(data, tuple):
                return ",".join(map(str, data))
            return data
        except KeyError:
            return "-"
    return '-'


def get_report_type(variant, hotspot):
    if isinstance(variant, pysam.VariantRecord):
        if hotspot.REPORT == ReportClass.region or hotspot.REPORT == ReportClass.region_all:
            return "3-check"
        if is_indel(variant) or is_multibp_sub(variant):
            return "2-indel"
    return "1-hotspot"


def get_sample_value(variant, sample):
    if isinstance(variant, pysam.VariantRecord):
        return variant.samples[sample]


def get_read_level(read_levels, rd):
    try:
        for (level, depth_status, analyzable) in read_levels:
            rd = int(rd)
            if rd >= int(level):
                return depth_status, analyzable
    except ValueError:
        pass
    return "-", "zero"


def is_indel(variant):
    if len(variant.alleles) != 2:
        raise Exception("Unhandled case: " + str(variant.alleles))
    return (len(variant.alleles[0]) == 1 and len(variant.alleles[1]) > 1) or \
           (len(variant.alleles[1]) == 1 and len(variant.alleles[0]) > 1)


def is_multibp_sub(variant):
    if len(variant.alleles) != 2:
        raise Exception("Unhandled case: " + str(variant.alleles))
    return len(variant.alleles[0]) > 1 and len(variant.alleles[1]) > 1


def clinical_flagged(variant):
    if isinstance(variant, pysam.VariantRecord):
        rs = get_info_field(variant, 'snp138').startswith("rs")
        nonflagged = get_info_field(variant, 'snp138NonFlagged')
        if rs and ("-" == nonflagged or nonflagged == "."):
            return "Yes"
        else:
            return "No"


def get_vaf(variant, sample):
    if isinstance(variant, pysam.VariantRecord):
        depth, ref, var = get_depth(variant, sample)
        return int(var)/(int(depth))
