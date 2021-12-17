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

    log.info("Processing variants")
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
                    log.debug("Adding variant {}:{}-{} {} {} to hotspot: {}".format(variant.chrom,
                                                                                    variant.start,
                                                                                    variant.stop,
                                                                                    variant.ref,
                                                                                    ",".join(variant.alts),
                                                                                    hotspot))
                    added = True
                    break
            if added:
                break
        if not added:
            other.append(variant)
    log.info("Open genomic vcf")
    g_variants = VariantFile(gvcf_file)
    sample_format_index_mapper = {sample: index + 1 for index, sample in enumerate(g_variants.header.samples)}

    columns = {'columns': []}
    if column_yaml_file is not None:
        log.info("Process yaml for: {}".format(column_yaml_file))
        with open(column_yaml_file) as file:
            columns = yaml.load(file, Loader=yaml.FullLoader)

    log.info("Process vcf header: {}".format(vcf_file))
    for record in variants.header.records:
        if record.type == "INFO":
            if record['ID'] == "CSQ":
                log.info(" -- found vep information: {}".format(vcf_file))
                log.debug(" -- -- {}".format(record['Description'].split("Format: ")[1].split("|")))
                vep_fields = {v: c for c, v in enumerate(record['Description'].split("Format: ")[1].split("|"))}
                annotation_extractor = utils.get_annoation_data_vep(vep_fields)

    log.info("open output file: {}".format(output))
    with open(output, "w") as writer:
        writer.write("sample\tchr\tstart\tend\treport\tgvcf_depth")
        log.info("Printing header: {}".format(output))
        for c in columns["columns"]:
            writer.write("\t{}".format(c))
        log.info("Printing hotspot information: {}".format(output))
        counter = 0
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
                            counter += 1
                    else:
                        # print found variants that overlap with hotspot positions
                        for var in variant['variants']:
                            depth = utils.get_depth(g_variants, sample, var.chrom, var.start, var.stop)
                            writer.write("\n{}\t{}\t{}\t{}\t{}\t{}\t{}".format(sample,
                                                                               chr_translater.get_nc_value(var.chrom),
                                                                               var.start + 1,
                                                                               var.stop,
                                                                               var.ref,
                                                                               ",".join(var.alts),
                                                                               utils.get_report_type(var, hotspot)))
                            writer.write("\t{}\t{}\t{}".format(depth,
                                                               var.samples[sample]['AD'][0],
                                                               ",".join(map(str, var.samples[sample]['AD'][1:]))))
                            print_columns(writer, var, hotspot, columns, annotation_extractor, depth, levels)
                            counter += 1
        log.info("-- hotspot entries: {}".format(counter))
        log.info("Printing variants that aren't hotspot: {}".format(output))
        counter = 0
        for var in other:
            # print variants that doesn't overlap with a hotspot
            writer.write("\n{}\t{}\t{}\t{}\t{}\t{}\t{}".format(sample,
                                                               chr_translater.get_nc_value(var.chrom),
                                                               var.start + 1,
                                                               var.stop,
                                                               var.ref,
                                                               ",".join(var.alts),
                                                               "4-other"))
            depth = utils.get_depth(g_variants, sample, var.chrom, var.start, var.stop)
            writer.write("\t{}\t{}\t{}".format(depth,
                                               var.samples[sample]['AD'][0],
                                               ",".join(map(str, var.samples[sample]['AD'][1:]))))
            print_columns(writer, var, None, columns, annotation_extractor, depth, levels)
            counter += 1
            log.info("-- non-hotspot entries: {}".format(counter))


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
