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


def generate_hotspot_report(sample,
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

    output_order = []
    hotspot_columns = ['sample', 'chr', 'start', 'stop', 'ref', 'alt', 'report', 'gvcf_depth', 'ref_depth', 'alt_depth']
    report_header = []

    biggest_order = -1
    for entry in columns['columns']:
        if 'order' in columns['columns'][entry]:
            if entry in hotspot_columns:
                hotspot_columns.remove(entry)
            output_order.append((columns['columns'][entry]['order'], entry))
            report_header.append((columns['columns'][entry]['order'], entry))
            biggest_order = max(biggest_order, columns['columns'][entry]['order'])
        elif columns['columns'][entry].get('visible', 1) == 0:
            if entry in hotspot_columns:
                hotspot_columns.remove(entry)
    for entry in hotspot_columns:

        biggest_order += 1
        output_order.append((biggest_order, entry))
        report_header.append((biggest_order, entry))
    for entry in columns['columns']:
        if 'order' not in columns['columns'][entry]:
            if columns['columns'][entry].get('visible', 1) == 0:
                continue
            biggest_order += 1
            output_order.append((biggest_order, entry))
            report_header.append((biggest_order, entry))
    output_order = sorted(output_order, key=lambda tup: tup[0])
    report_header = sorted(report_header, key=lambda tup: tup[0])

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
        writer.write("\t".join([name[1] for name in report_header]))
        log.info("Printing header: {}".format(output))
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
                            data = {'sample': sample,
                                    'chr': hotspot.CHROMOSOME,
                                    'start': hotspot.EXTENDED_START + index,
                                    'stop': hotspot.EXTENDED_START + index,
                                    'ref': '-',
                                    'alt': '-',
                                    'report':  hotspot.REPORT,
                                    'gvcf_depth': depth,
                                    'ref_depth': '-',
                                    'alt_depth': '-'}
                            add_columns(data, None, hotspot, columns, annotation_extractor, depth, levels)
                            writer.write("\n" + "\t".join([str(data[c[1]]) for c in output_order]))
                            counter += 1
                    else:
                        # print found variants that overlap with hotspot positions
                        for var in variant['variants']:
                            depth = utils.get_depth(g_variants, sample, var.chrom, var.start, var.stop)
                            data = {'sample': sample,
                                    'chr': chr_translater.get_nc_value(var.chrom),
                                    'start': var.start + 1,
                                    'stop': var.stop,
                                    'ref': var.ref,
                                    'alt': ",".join(var.alts),
                                    'report': utils.get_report_type(var, hotspot),
                                    'gvcf_depth': depth,
                                    'ref_depth': var.samples[sample]['AD'][0],
                                    'alt_depth': ",".join(map(str, var.samples[sample]['AD'][1:]))}
                            add_columns(data, var, hotspot, columns, annotation_extractor, depth, levels)
                            writer.write("\n" + "\t".join([str(data[c[1]]) for c in output_order]))
                            counter += 1
        log.info("-- hotspot entries: {}".format(counter))
        log.info("Printing variants that aren't hotspot: {}".format(output))
        counter = 0
        for var in other:
            # print variants that doesn't overlap with a hotspot
            depth = utils.get_depth(g_variants, sample, var.chrom, var.start, var.stop)
            data = {'sample': sample,
                    'chr': chr_translater.get_nc_value(var.chrom),
                    'start': var.start + 1,
                    'stop': var.stop,
                    'ref': var.ref,
                    'alt': ",".join(var.alts),
                    'report': "4-other",
                    'gvcf_depth': depth,
                    'ref_depth': var.samples[sample]['AD'][0],
                    'alt_depth': ",".join(map(str, var.samples[sample]['AD'][1:]))}
            add_columns(data, var, None, columns, annotation_extractor, depth, levels)
            writer.write("\n" + "\t".join([str(data[c[1]]) for c in output_order]))
            counter += 1
            log.info("-- non-hotspot entries: {}".format(counter))


def add_columns(data, var, hotspot, columns, annotation_extractor, depth, levels):
    """
        print extra columns defined by a yaml file. Data from variant, hotspot or annotations
    """
    for c in columns["columns"]:
        if 'from' in columns["columns"][c]:
            if columns["columns"][c]['from'] == "vep":
                data[c] = annotation_extractor(var,  columns["columns"][c]['field'])
            elif columns["columns"][c]['from'] == "hotspot":
                if hotspot is None:
                    data[c] = "-"
                else:
                    data[c] = getattr(hotspot, columns["columns"][c]['field'])
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
                    data[c] = value[columns["columns"][c]['column']]
                else:
                    data[c] = value
            elif columns["columns"][c]['from'] == 'variable':
                data[c] = locals()[columns["columns"][c]['field']]
            else:
                raise Exception("Undhandledd cased: " + columns["columns"][c]['field'])
