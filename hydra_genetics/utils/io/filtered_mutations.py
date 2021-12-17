import logging
from collections import OrderedDict

from hydra_genetics.utils.io.chr import ChrTranslater
from hydra_genetics.utils.models.hotspot import MultiBpVariantData
from hydra_genetics.utils.models.hotspot import ReportClass
from hydra_genetics.utils.io.hotspot import Reader as HotspotReader
from hydra_genetics.utils.io import utils

from pysam import VariantFile

import yaml

log = logging.getLogger()


def generate_filtered_mutations(sample,
                                caller,
                                output,
                                levels,
                                hotspot_file,
                                vcf_file,
                                gvcf_file,
                                chr_mapping,
                                column_yaml_file=None):
    reports = OrderedDict(((ReportClass.hotspot, []),
                          (ReportClass.region_all, []),
                          (ReportClass.region, []),
                          (ReportClass.indel, [])))
    if not hotspot_file == "-":
        hotspot_reader = HotspotReader(hotspot_file)
        for hotspot in iter(hotspot_reader):
            reports[hotspot.REPORT].append(hotspot)
    chr_translater = ChrTranslater(chr_mapping)
    variants = VariantFile(vcf_file)
    other = []

    for variant in variants:
        # ToDo make sure that empty variants are handled better!!!
        if variant is None:
            raise Exception("Empty allele found: " + str(variant))
            continue
        if not len(variant.alts) == 1:
            raise Exception("Multiple allele found: " + str(variant.alts))
        added = False
        for report in reports:
            for hotspot in reports[report]:
                if hotspot.add_variant(variant, chr_translater):
                    added = True
                    break
            if added:
                break
        if not added:
            other.append(variant)
    g_variants = VariantFile(gvcf_file)
    sample_format_index_mapper = {sample: index + 1 for index, sample in enumerate(g_variants.header.samples)}

    columns = {'columns': []}
    if column_yaml_file is not None:
        with open(column_yaml_file) as file:
            columns = yaml.load(file, Loader=yaml.FullLoader)

    for record in variants.header.records:
        if record.type == "INFO":
            if record['ID'] == "CSQ":
                vep_fields = {v: c for c, v in enumerate(record['Description'].split("Format: ")[1].split("|"))}
                annotation_extractor = utils.get_annoation_data_vep(vep_fields)

    with open(output, "w") as writer:
        writer.write("sample\tchr\tstart\tend\treport\tgvcf_depth")
        for c in columns["columns"]:
            if "fields" in columns["columns"][c]:
                for sub_field in columns["columns"][c]['fields']:
                    writer.write("\t{}".format(sub_field))
            else:
                writer.write("\t{}".format(c))
        for report in reports:
            for hotspot in reports[report]:
                for index, variant in enumerate(hotspot.VARIANTS):
                    # even though no variants were found print hotspot and region all entries
                    if not variant['variants'] and not variant['extended']:
                        depth = utils.get_depth(g_variants,
                                                sample,
                                                chr_translater.get_chr_value(hotspot.CHROMOSOME),
                                                hotspot.EXTENDED_START + index - 1,
                                                hotspot.EXTENDED_START + index)
                        if hotspot.REPORT == ReportClass.region_all and depth > 299:
                            continue
                        elif hotspot.ALWAYS_PRINT:
                            writer.write("\n{}\t{}\t{}\t{}\t{}\t{}\t{}".format(sample,
                                                                               hotspot.CHROMOSOME,
                                                                               hotspot.EXTENDED_START + index,
                                                                               hotspot.EXTENDED_START + index,
                                                                               "-",
                                                                               "-",
                                                                               hotspot.REPORT))
                            writer.write("\t{}\t{}\t{}".format(depth, "-", "-"))
                            print_columns(writer, variant, hotspot, columns, annotation_extractor, depth, levels)
                    else:
                        # print found variants that overlap with hotspot positions
                        for var in variant['variants']:
                            depth = utils.get_depth(g_variants, sample, var.chrom, var.start, var.stop)
                            writer.write("\n{}\t{}\t{}\t{}\t{}\t{}\t{}".format(sample,
                                                                               chr_translater.get_nc_value(var.chrom),
                                                                               var.start,
                                                                               var.stop - 1,
                                                                               var.ref,
                                                                               ",".join(var.alts),
                                                                               utils.get_report_type(var, hotspot)))
                            writer.write("\t{}\t{}\t{}".format(depth,
                                                               var.samples[sample]['AD'][0],
                                                               ",".join(map(str, var.samples[sample]['AD'][1:]))))
                            print_columns(writer, var, hotspot, columns, annotation_extractor, depth, levels)
        for var in other:
            # print variants that doesn't overlap with a hotspot
            writer.write("\n{}\t{}\t{}\t{}\t{}\t{}\t{}".format(sample,
                                                               chr_translater.get_nc_value(var.chrom),
                                                               var.start,
                                                               var.stop - 1,
                                                               var.ref,
                                                               ",".join(var.alts),
                                                               "4-other"))
            depth = utils.get_depth(g_variants, sample, var.chrom, var.start, var.stop)
            writer.write("\t{}\t{}\t{}".format(depth,
                                               var.samples[sample]['AD'][0],
                                               ",".join(map(str, var.samples[sample]['AD'][1:]))))
            print_columns(writer, var, None, columns, annotation_extractor, depth, levels)


def print_columns(writer, var, hotspot, columns, annotation_extractor, depth, levels):
    """
        print extra columns defined by a yaml file. Data from variant, hotspot or annotations
    """
    for c in columns["columns"]:
        if columns["columns"][c]['from'] == "vep":
            writer.write("\t{}".format(annotation_extractor(var,  columns["columns"][c]['field'])))
        elif columns["columns"][c]['from'] == "hotspot":
            if hotspot is None:
                writer.write("\t-")
            else:
                writer.write("\t{}".format(getattr(hotspot, columns["columns"][c]['field'])))
        elif columns["columns"][c]['from'] == "function":
            function = getattr(utils, columns["columns"][c]['name'])
            variables = ()
            if 'variables' in columns["columns"][c]:
                variables = []
                for v in columns["columns"][c]['variables']:
                    variables.append(locals().get(v, v))
                value = function(*variables)
            else:
                function()
            if 'column' in columns["columns"][c]:
                writer.write("\t{}".format(value[columns["columns"][c]['column']]))
            else:
                writer.write("\t{}".format(value))
        elif columns["columns"][c]['from'] == 'variable':
            writer.write("\t{}".format(locals()[columns["columns"][c]['field']]))
        else:
            raise Exception("Undhandledd cased: " + columns["columns"][c]['field'])
