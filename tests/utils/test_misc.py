# coding: utf-8

import unittest
import yaml
import types
from hydra_genetics.utils.misc import get_longread_bam, get_input_aligned_bam, get_input_haplotagged_bam
from snakemake.sourcecache import WorkflowError


class TestResourcesUtils(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_merge(self):
        from hydra_genetics.utils.misc import merge
        dict1a = {'bwa_mem': {'extra': "some settings"}}
        dict1b = {'bwa_mem': {'extra': "some settings"}}
        dict2 = {'bwa_mem': {'cpu': 20, 'time': '12:00:00'}}
        dict1a.update(dict2)
        self.assertEqual({'bwa_mem': {'cpu': 20, 'time': '12:00:00'}}, dict1a)
        dict1b = merge(dict1b, dict2)
        self.assertEqual({'bwa_mem': {'extra': "some settings", 'cpu': 20, 'time': '12:00:00'}}, dict1b)

    def test_extract_chr(self):
        from hydra_genetics.utils.misc import extract_chr
        self.assertEqual(extract_chr("tests/utils/files/ref.fasta.fai"), [
                                     'chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9', 'chr10', 'chr11',
                                     'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17', 'chr18', 'chr19', 'chr20', 'chr21',
                                     'chr22', 'chrX', 'chrY'])
        self.assertEqual(extract_chr("tests/utils/files/ref.fasta.fai", ['chr6', 'chr17', 'chrX']), [
                                     'chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr7', 'chr8', 'chr9', 'chr10', 'chr11', 'chr12',
                                     'chr13', 'chr14', 'chr15', 'chr16', 'chr18', 'chr19', 'chr20', 'chr21', 'chr22', 'chrY',
                                     'chrM'])
        self.assertEqual(extract_chr(""), [''])

    def test_variable_replacement(self):
        with open("tests/utils/files/config_variable_replacement.yaml") as f:
            config = yaml.load(f, Loader=yaml.loader.SafeLoader)
        print(config)
        self.assertEqual(config,
                         {'PROJECT': 'MY variable', 'bwa_mem': {'extra': 'some settings {{PROJECT}}'}})

        from hydra_genetics.utils.misc import replace_dict_variables
        self.assertEqual(replace_dict_variables(config),
                         {'PROJECT': 'MY variable', 'bwa_mem': {'extra': 'some settings MY variable'}})


class TestGetInputAlignedBam(unittest.TestCase):
    def test_get_longread_bam(self):
        # Test with default aligner
        config = {}
        wildcards = types.SimpleNamespace(sample="sample1", type="T")
        bam, bai = get_longread_bam(wildcards, config)
        self.assertEqual(bam, "alignment/minimap2_align/sample1_T.bam")
        self.assertEqual(bai, "alignment/minimap2_align/sample1_T.bam.bai")
        # Test with custom aligner
        config = {"aligner": "pbmm2"}
        wildcards = types.SimpleNamespace(sample="sample2", type="N")
        bam, bai = get_longread_bam(wildcards, config)
        self.assertEqual(bam, "alignment/pbmm2_align/sample2_N.bam")
        self.assertEqual(bai, "alignment/pbmm2_align/sample2_N.bam.bai")

    def test_with_aligner(self):
        config = {"aligner": "minimap2"}
        wildcards = types.SimpleNamespace(sample="S1", type="T")
        bam, bai = get_input_aligned_bam(wildcards, config)
        self.assertEqual(bam, "alignment/minimap2_align/S1_T.bam")
        self.assertEqual(bai, "alignment/minimap2_align/S1_T.bam.bai")

    def test_without_aligner(self):
        config = {}
        wildcards = types.SimpleNamespace(sample="S2", type="N")
        bam, bai = get_input_aligned_bam(wildcards, config)
        self.assertEqual(bam, "alignment/samtools_merge_bam/S2_N.bam")
        self.assertEqual(bai, "alignment/samtools_merge_bam/S2_N.bam.bai")

    def test_custom_default_path(self):
        config = {}
        wildcards = types.SimpleNamespace(sample="S3", type="T")
        bam, bai = get_input_aligned_bam(wildcards, config, default_path="custom/path")
        self.assertEqual(bam, "custom/path/S3_T.bam")
        self.assertEqual(bai, "custom/path/S3_T.bam.bai")

    def test_missing_sample_key(self):
        config = {}
        wildcards = types.SimpleNamespace(type="T")
        with self.assertRaises(Exception):
            get_input_aligned_bam(wildcards, config)

    def test_missing_type_key(self):
        config = {}
        wildcards = types.SimpleNamespace(sample="S4")
        with self.assertRaises(Exception):
            get_input_aligned_bam(wildcards, config)


class TestGetInputHaplotaggedBam(unittest.TestCase):
    def test_default_path_only(self):
        wildcards = types.SimpleNamespace(sample="S10", type="N")
        config = dict()
        bam, bai = get_input_haplotagged_bam(
            wildcards,
            config,
            default_path="custom/default/path"
        )
        self.assertEqual(bam, "custom/default/path/S10_N.bam")
        self.assertEqual(bai, "custom/default/path/S10_N.bam.bai")

    def test_missing_type_wildcard(self):
        wildcards = types.SimpleNamespace(sample="S11")
        config = dict()
        with self.assertRaises(WorkflowError):
            get_input_haplotagged_bam(wildcards, config)

    def test_missing_sample_wildcard(self):
        wildcards = types.SimpleNamespace(type="T")
        config = dict()
        with self.assertRaises(WorkflowError):
            get_input_haplotagged_bam(wildcards, config)

    def test_empty_haplotag_path(self):
        wildcards = types.SimpleNamespace(sample="S12", type="T")
        config = dict({'haplotag_path': ""})
        bam, bai = get_input_haplotagged_bam(
            wildcards,
            config
        )
        self.assertEqual(bam, "S12_T.bam")
        self.assertEqual(bai, "S12_T.bam.bai")

    def test_missing_haplotag_path(self):
        wildcards = types.SimpleNamespace(sample="S14", type="N")
        config = dict()
        bam, bai = get_input_haplotagged_bam(
            wildcards,
            config
        )
        self.assertEqual(bam, "alignment/samtools_merge_bam/S14_N.bam")
        self.assertEqual(bai, "alignment/samtools_merge_bam/S14_N.bam.bai")

    def test_default_values(self):
        wildcards = types.SimpleNamespace(sample="S13", type="N")
        config = dict()
        bam, bai = get_input_haplotagged_bam(wildcards, config)
        self.assertEqual(bam, "alignment/samtools_merge_bam/S13_N.bam")
        self.assertEqual(bai, "alignment/samtools_merge_bam/S13_N.bam.bai")

    def test_with_custom_suffix(self):
        wildcards = types.SimpleNamespace(sample="S5", type="T")
        config = dict({"haplotag_path": "snv_indels/whatshap_haplotag"})
        bam, bai = get_input_haplotagged_bam(
            wildcards,
            config,
            suffix="custom_suffix"
        )
        self.assertEqual(bam, "snv_indels/whatshap_haplotag/S5_T.custom_suffix.bam")
        self.assertEqual(bai, "snv_indels/whatshap_haplotag/S5_T.custom_suffix.bam.bai")

    def test_with_suffix_in_config(self):
        wildcards = types.SimpleNamespace(sample="S7", type="N")
        config = dict({
            "haplotag_path": "snv_indels/whatshap_haplotag",
            "haplotag_suffix": "from_config"
        })
        bam, bai = get_input_haplotagged_bam(
            wildcards,
            config
        )
        self.assertEqual(bam, "snv_indels/whatshap_haplotag/S7_N.from_config.bam")
        self.assertEqual(bai, "snv_indels/whatshap_haplotag/S7_N.from_config.bam.bai")

    def test_with_empty_suffix(self):
        wildcards = types.SimpleNamespace(sample="S6", type="T")
        config = dict({"haplotag_path": "snv_indels/whatshap_haplotag"})
        bam, bai = get_input_haplotagged_bam(
            wildcards, 
            config,
            suffix=""
        )
        self.assertEqual(bam, "snv_indels/whatshap_haplotag/S6_T.bam")
        self.assertEqual(bai, "snv_indels/whatshap_haplotag/S6_T.bam.bai")

    def test_with_all_parameters(self):
        wildcards = types.SimpleNamespace(sample="S8", type="T")
        config = dict({"haplotag_path": "custom/path"})
        bam, bai = get_input_haplotagged_bam(
            wildcards,
            config,
            default_path="should/not/use",
            suffix="special"
        )
        self.assertEqual(bam, "custom/path/S8_T.special.bam")
        self.assertEqual(bai, "custom/path/S8_T.special.bam.bai")

    def test_none_suffix(self):
        wildcards = types.SimpleNamespace(sample="S9", type="N")
        config = dict({"haplotag_path": "custom/path"})
        bam, bai = get_input_haplotagged_bam(
            wildcards,
            config,
            suffix=None
        )
        self.assertEqual(bam, "custom/path/S9_N.bam")
        self.assertEqual(bai, "custom/path/S9_N.bam.bai")
