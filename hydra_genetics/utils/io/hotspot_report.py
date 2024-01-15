import builtins
import logging
import statistics
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
                            vcf_file_wo_pick=None,
                            column_yaml_file=None):
    reports = OrderedDict(((ReportClass.hotspot, {}),
                          (ReportClass.region_all, {}),
                          (ReportClass.region, {}),
                          (ReportClass.indel, {'indel': []})))
    chr_translater = ChrTranslater(chr_mapping)

    chromosomes_to_look_at = set()
    if not hotspot_file == "-":
        try:
            hotspot_reader = HotspotReader(hotspot_file)
            for hotspot in iter(hotspot_reader):
                chromosomes_to_look_at.add(chr_translater.get_chr_value(hotspot.CHROMOSOME))
                if hotspot.REPORT == ReportClass.indel:
                    reports[hotspot.REPORT]['indel'].append(hotspot)
                else:
                    key = f"{hotspot.CHROMOSOME}-{hotspot.START // 1000000}"
                    reports[hotspot.REPORT][key] = reports[hotspot.REPORT].get(key, []) + [hotspot]
        except ValueError as e:
            logging.error(e)
            exit(1)

    variants = VariantFile(vcf_file)
    other = []

    transcript_dict = {}
    log.info("Processing vep transcripts")
    for record in variants.header.records:
        if record.type == "INFO":
            if record['ID'] == "CSQ":
                vep_fields = {v: c for c, v in enumerate(record['Description'].split("Format: ")[1].split("|"))}

    for variant in variants:
        if variant is None:
            raise Exception("Empty allele found: " + str(variant))
        if not len(variant.alts) == 1:
            raise Exception("Multiple allele found: " + str(variant.alts))
        chromosomes_to_look_at.add(variant.chrom)
        variant_key = f"{variant.chrom}_{variant.start}_{variant.stop}_{variant.ref}_{','.join(variant.alts)}"
        transcript = variant.info['CSQ'][0].split("|")[vep_fields['Feature']]
        transcript_dict[variant_key] = transcript

    if vcf_file_wo_pick is not None:
        variants = VariantFile(vcf_file_wo_pick)
    else:
        variants = VariantFile(vcf_file)
    log.info("Processing variants")
    sub_report_keys = list(reports.keys())[0:-1]
    indel_report_key = list(reports.keys())[-1]
    for variant in variants:
        # ToDo make sure that empty variants are handled better!!!
        if variant is None:
            raise Exception("Empty allele found: " + str(variant))
        if not len(variant.alts) == 1:
            raise Exception("Multiple allele found: " + str(variant.alts))
        variant_key = f"{variant.chrom}_{variant.start}_{variant.stop}_{variant.ref}_{','.join(variant.alts)}"
        variant_key_hotspot = f"{chr_translater.get_nc_value(variant.chrom)}-{variant.start // 1000000}"
        if variant_key in transcript_dict:
            added = False
            for report in sub_report_keys:
                for hotspot in reports[report].get(variant_key_hotspot, []):
                    if hotspot.add_variant(variant, chr_translater):
                        hotspot_transcript = hotspot.ACCESSION_NUMBER
                        if not hotspot_transcript == "-":
                            transcript_dict[variant_key] = hotspot_transcript
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
                for hotspot in reports[indel_report_key]['indel']:
                    if hotspot.add_variant(variant, chr_translater):
                        hotspot_transcript = hotspot.ACCESSION_NUMBER
                        if not hotspot_transcript == "-":
                            transcript_dict[variant_key] = hotspot_transcript
                        log.debug("Adding variant {}:{}-{} {} {} to hotspot: {}".format(variant.chrom,
                                                                                        variant.start,
                                                                                        variant.stop,
                                                                                        variant.ref,
                                                                                        ",".join(variant.alts),
                                                                                        hotspot))
                        added = True
                        break
            if not added:
                chromosomes_to_look_at.add(variant.chrom)
                other.append(variant)
    log.info("Open genomic vcf")
    g_variants = VariantFile(gvcf_file)

    columns = {'columns': []}
    if column_yaml_file is not None:
        log.info("Process yaml for: {}".format(column_yaml_file))
        with open(column_yaml_file) as file:
            columns = yaml.load(file, Loader=yaml.FullLoader)

    output_order = []
    hotspot_columns = {'sample': {},
                       'chr': {},
                       'start': {},
                       'stop': {},
                       'ref': {},
                       'alt': {},
                       'report': {},
                       'gvcf_depth': {},
                       'ref_depth': {},
                       'alt_depth': {}}
    report_header = []

    biggest_order = -1

    gcvf_depth_field = 'DP'
    if isinstance(columns['columns'], dict):
        gcvf_depth_field = columns['columns'].get('gvcf_depth', {}).get('field', 'DP')
    for entry in columns['columns']:
        if entry in hotspot_columns:
            if columns['columns'][entry].get('visible', 1) == 0 or 'order' in columns['columns'][entry]:
                del hotspot_columns[entry]
            elif columns['columns'][entry].get('format', None):
                hotspot_columns[entry]['format'] = columns['columns'][entry]['format']
        if 'order' in columns['columns'][entry]:
            output_order.append((columns['columns'][entry]['order'], entry))
            if 'from' in columns['columns'][entry] and 'merge' == columns['columns'][entry]['from']:
                report_header.append((columns['columns'][entry]['order'],
                                      entry + "_" +
                                      columns['columns'][entry]['divider'].join(
                                        extract_item_merge_header(columns['columns'][entry]['elements']))))
            else:
                report_header.append((columns['columns'][entry]['order'], entry))
            biggest_order = max(biggest_order, columns['columns'][entry]['order'])
    for key in hotspot_columns:
        if key in columns['columns']:
            del columns['columns'][key]

    depth_data = dict(map(lambda x: (x, {}), chromosomes_to_look_at))

    for chr in depth_data:
        for variant in g_variants.fetch(chr):
            depth_data[chr][variant.start] = variant.samples[sample][gcvf_depth_field]

    def handle_select(data):
        def convert_list_slice(info):
            if len(info) < 3:
                raise SyntaxError(f"Invalid syntax: {info}")
            if info.startswith("[") and info.endswith("]"):
                info = info[1:-1].split(":")
                if len(info) == 1:
                    return lambda data: data[int(info[0])]
                elif len(info) == 2:
                    value0 = int(info[0]) if len(info[0]) > 0 else None
                    value1 = int(info[1]) if len(info[1]) > 0 else None
                    return lambda data: data[value0:value1]
                elif len(info) == 3:
                    value0 = int(info[0]) if len(info[0]) > 0 else None
                    value1 = int(info[1]) if len(info[1]) > 0 else None
                    value2 = int(info[2]) if len(info[2]) > 0 else None
                    return lambda data: data[value0:value1:value2]
                else:
                    raise SyntaxError(f"Invalid syntax: {info}, invalid number of elements inside '[]'")
            else:
                raise SyntaxError(f"Invalid syntax: {info}, missing bracket '[]'")

        def condition(items, empty):
            items = convert_list_slice(items)

            def func(data):
                values = items(data)
                if isinstance(values, str):
                    return (values == "-") == empty
                else:
                    return (len([v for _, v in values.items() if v != "-"]) == 0) == empty
            return func

        data['items'] = convert_list_slice(data['items'])
        if "else" in data:
            data['else'] = convert_list_slice(data['else'])
        if "condition" in data:
            data['condition'] = condition(data['condition']['items'], data['condition'].get("empty", True))
        return data

    for entry in columns['columns']:
        if "from" in columns['columns'][entry] and "select" in columns['columns'][entry]["from"]:
            columns['columns'][entry] = handle_select(columns['columns'][entry])

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
            if 'from' in columns['columns'][entry] and 'merge' == columns['columns'][entry]['from']:
                report_header.append((biggest_order,
                                      entry + "_" +
                                      columns['columns'][entry]['divider'].join(
                                        extract_item_merge_header(columns['columns'][entry]['elements']))))
            else:
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
                annotation_extractor = utils.get_annotation_data_vep(vep_fields, transcript_dict)

    def get_depth(data, chr, start, stop):
        depth = [data[chr].get(pos, 0) for pos in range(start, stop)]
        if len(depth) > 1:
            return statistics.mean(depth)
        elif len(depth) == 1:
            return depth[0]
        else:
            return 0

    log.info("open output file: {}".format(output))
    with open(output, "w") as writer:
        writer.write("\t".join([name[1] for name in report_header]))
        log.info("Printing header: {}".format(output))
        log.info("Printing hotspot information: {}".format(output))
        counter = 0
        for report in reports:
            for index_data in reports[report]:
                for hotspot in reports[report][index_data]:
                    for index, variant in enumerate(hotspot.VARIANTS):
                        # even though no variants were found print hotspot and region all entries
                        if not variant['variants'] and not variant['extended']:
                            depth = get_depth(depth_data,
                                              chr_translater.get_chr_value(hotspot.CHROMOSOME),
                                              hotspot.EXTENDED_START + index-1,
                                              hotspot.EXTENDED_START + index)
                            if hotspot.REPORT == ReportClass.region_all and depth > 299:  # ToDo remove harcoded value
                                continue
                            elif hotspot.ALWAYS_PRINT:
                                data = {'sample': sample,
                                        'chr': hotspot.CHROMOSOME,
                                        'start': hotspot.EXTENDED_START + index,
                                        'stop': hotspot.EXTENDED_START + index,
                                        'ref': '-',
                                        'alt': '-',
                                        'report':  utils.format_report_type(hotspot),
                                        'gvcf_depth': depth,
                                        'ref_depth': '-',
                                        'alt_depth': '-'}
                                format_hotspot(data, columns, hotspot_columns)
                                add_columns(data, None, hotspot, columns, annotation_extractor, depth, levels)
                                writer.write("\n" + "\t".join([str(data[c[1]]) for c in output_order]))
                                counter += 1
                        else:
                            # print found variants that overlap with hotspot positions
                            for var in variant['variants']:
                                depth = get_depth(depth_data,
                                                  var.chrom,
                                                  var.start,
                                                  var.stop)
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
                                format_hotspot(data, columns, hotspot_columns)
                                add_columns(data, var, hotspot, columns, annotation_extractor, depth, levels)
                                writer.write("\n" + "\t".join([str(data[c[1]]) for c in output_order]))
                                counter += 1
        log.info("-- hotspot entries: {}".format(counter))
        log.info("Printing variants that aren't hotspot: {}".format(output))
        counter = 0
        for var in other:
            # print variants that doesn't overlap with a hotspot
            depth = get_depth(depth_data,
                              var.chrom,
                              var.start,
                              var.stop)
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
            format_hotspot(data, columns, hotspot_columns)
            add_columns(data, var, None, columns, annotation_extractor, depth, levels)
            writer.write("\n" + "\t".join([str(data[c[1]]) for c in output_order]))
            counter += 1
            log.info("-- non-hotspot entries: {}".format(counter))


def format_value(value, format):
    if format[0] == "replace":
        return value.replace(format[1], format[2])
    elif format[0] == "string":
        if len(format) == 3:
            value = getattr(builtins, format[2])(value)
        else:
            value = float(value)
        return format[1].format(value)
    else:
        raise Exception("Unknown format value: " + format)


def format_hotspot(data, columns, hotspot):
    for key in data:
        format = columns.get(key, {}).get("format", None)
        format = hotspot.get(key, {}).get("format", format)
        if format:
            try:
                data[key] = format_value(data[key], format)
            except ValueError:
                log.warning("Unable to format value {}, field {}, format {}".format(data[key], key, format))
            except TypeError:
                log.warning("Unable to format value {}, field {}, format {}".format(data[key], key, format))


def extract_item_merge_header(columns):
    header_list = []
    for value in columns:
        if 'from' in columns[value] and columns[value]['from'] == 'merge':
            header_list.append(value + "_" +
                               columns[value]['divider'].join(extract_item_merge_header(columns[value]['elements'])))
        else:
            header_list.append(value)
    return header_list


def add_columns(data, var, hotspot, columns, annotation_extractor, depth, levels):
    """
        print extra columns defined by a yaml file. Data from variant, hotspot or annotations
    """
    def add_data(data, column, c, depth, levels):
        if column[c]['from'] == "merge":
            # Used to merge two columns and combine using divider
            divider = column[c]['divider']
            temp_data = OrderedDict()
            for key in column[c]['elements']:
                add_data(temp_data, column[c]['elements'], key, depth, levels)
            data[c] = divider.join([v for k, v in temp_data.items()])
        elif column[c]['from'] == "select":
            # From multiple column select the first one with data
            temp_data = OrderedDict()
            for key in column[c]['elements']:
                add_data(temp_data, column[c]['elements'], key, depth, levels)
            temp_data = [v for _, v in temp_data.items()]
            select = column[c]['items'](temp_data)
            if not isinstance(select, str):
                select = column[c].get("divider", ":").join(select)
            data[c] = "-"
            condition = True
            if 'condition' in column[c]:
                condition = column[c]['condition'](temp_data)
            if select is not None and select != '-' and condition:
                data[c] = select
            elif 'else' in column[c]:
                select = column[c]['else'](temp_data)
                if not isinstance(select, str):
                    select = [v for v in select if v != "-"]
                    if len(select) == 0:
                        select = "-"
                    else:
                        select = column[c].get("divider", ":").join(select)
                data[c] = select
        elif column[c]['from'] == "vep":
            try:
                data[c] = annotation_extractor(var,  column[c]['field'])
                if data[c] is None or data[c] == "":
                    data[c] = '-'
            except AttributeError:
                data[c] = '-'
            if "extract_regex" in column[c]:
                data[c] = utils.regex_extract(data[c], column[c]['extract_regex'])
        elif column[c]['from'] == "hotspot":
            if hotspot is None:
                data[c] = "-"
            else:
                data[c] = getattr(hotspot, column[c]['field'])
        elif column[c]['from'] == "function":
            function = getattr(utils, column[c]['name'])
            variables = ()
            if 'variables' in column[c]:
                variables = []
                for v in column[c]['variables']:
                    variables.append(locals().get(v, v))
                try:
                    value = function(*variables)
                except AttributeError:
                    value = "-"
            else:
                value = function()
            if 'column' in column[c]:
                data[c] = value[column[c]['column']]
            else:
                if isinstance(value, tuple):
                    value = ",".join(value)
                data[c] = value
            if data[c] is None:
                data[c] = "-"
        elif column[c]['from'] == 'variable':
            data[c] = locals()[column[c]['field']]
        else:
            raise Exception("Undhandledd cased: " + column[c]['field'])
        if "format" in column[c]:
            try:
                data[c] = format_value(data[c], column[c]["format"])
            except ValueError:
                log.debug("Unable to format value {}, field {}, format {}".format(data[c], c, column[c]["format"]))
            except TypeError:
                log.debug("Unable to format value {}, field {}, format {}".format(data[c], c, column[c]["format"]))

    for c in columns['columns']:
        if 'from' in columns['columns'][c]:
            add_data(data, columns['columns'], c, depth, levels)
