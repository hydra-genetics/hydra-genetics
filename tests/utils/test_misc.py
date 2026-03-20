# coding: utf-8

import unittest
import yaml
import types
from snakemake.sourcecache import WorkflowError
from hydra_genetics.utils.misc import get_input_aligned_bam, get_input_haplotagged_bam


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
    def test_with_aligner_in_dict(self):
        """Test aligner that exists in ALIGNER_PATHS dictionary"""
        config = {"aligner": "minimap2"}
        wildcards = types.SimpleNamespace(sample="S1", type="T")
        bam, bai = get_input_aligned_bam(wildcards, config)
        self.assertEqual(bam, "alignment/minimap2_align/S1_T.bam")
        self.assertEqual(bai, "alignment/minimap2_align/S1_T.bam.bai")

    def test_with_custom_aligner_path(self):
        """Test aligner with custom path in ALIGNER_PATHS"""
        config = {"aligner": "parabricks_fq2bam"}
        wildcards = types.SimpleNamespace(sample="S1", type="N")
        bam, bai = get_input_aligned_bam(wildcards, config)
        self.assertEqual(bam, "parabricks/pbrun_fq2bam/S1_N.bam")
        self.assertEqual(bai, "parabricks/pbrun_fq2bam/S1_N.bam.bai")

    def test_with_aligner_not_in_dict(self):
        """Test aligner not in ALIGNER_PATHS uses default pattern"""
        config = {"aligner": "bwa-mem2"}
        wildcards = types.SimpleNamespace(sample="S1", type="T")
        bam, bai = get_input_aligned_bam(wildcards, config)
        self.assertEqual(bam, "alignment/bwa-mem2_align/S1_T.bam")
        self.assertEqual(bai, "alignment/bwa-mem2_align/S1_T.bam.bai")

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

    def test_aligner_none_uses_default(self):
        """Test explicit None aligner uses default path"""
        config = {"aligner": None}
        wildcards = types.SimpleNamespace(sample="S4", type="T")
        bam, bai = get_input_aligned_bam(wildcards, config)
        self.assertEqual(bam, "alignment/samtools_merge_bam/S4_T.bam")
        self.assertEqual(bai, "alignment/samtools_merge_bam/S4_T.bam.bai")

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

    def test_set_type_override_N(self):
        """Test set_type='N' overrides wildcards.type"""
        config = {"aligner": "minimap2"}
        wildcards = types.SimpleNamespace(sample="S5", type="T")
        bam, bai = get_input_aligned_bam(wildcards, config, set_type="N")
        self.assertEqual(bam, "alignment/minimap2_align/S5_N.bam")
        self.assertEqual(bai, "alignment/minimap2_align/S5_N.bam.bai")

    def test_set_type_override_T(self):
        """Test set_type='T' overrides wildcards.type"""
        config = {}
        wildcards = types.SimpleNamespace(sample="S6", type="N")
        bam, bai = get_input_aligned_bam(wildcards, config, set_type="T")
        self.assertEqual(bam, "alignment/samtools_merge_bam/S6_T.bam")
        self.assertEqual(bai, "alignment/samtools_merge_bam/S6_T.bam.bai")

    def test_set_type_override_R(self):
        """Test set_type='R' overrides wildcards.type"""
        config = {"aligner": "pbmm2"}
        wildcards = types.SimpleNamespace(sample="S7", type="N")
        bam, bai = get_input_aligned_bam(wildcards, config, set_type="R")
        self.assertEqual(bam, "alignment/pbmm2_align/S7_R.bam")
        self.assertEqual(bai, "alignment/pbmm2_align/S7_R.bam.bai")

    def test_set_type_none_uses_wildcard(self):
        """Test set_type=None uses wildcards.type"""
        config = {"aligner": "minimap2"}
        wildcards = types.SimpleNamespace(sample="S8", type="T")
        bam, bai = get_input_aligned_bam(wildcards, config, set_type=None)
        self.assertEqual(bam, "alignment/minimap2_align/S8_T.bam")
        self.assertEqual(bai, "alignment/minimap2_align/S8_T.bam.bai")

    def test_set_type_invalid_value(self):
        """Test invalid set_type raises ValueError"""
        config = {"aligner": "minimap2"}
        wildcards = types.SimpleNamespace(sample="S9", type="T")
        with self.assertRaises(ValueError) as context:
            get_input_aligned_bam(wildcards, config, set_type="X")
        self.assertIn("set_type must be None, 'N', 'T', or 'R'", str(context.exception))

    def test_set_type_invalid_lowercase(self):
        """Test lowercase set_type raises ValueError"""
        config = {}
        wildcards = types.SimpleNamespace(sample="S10", type="T")
        with self.assertRaises(ValueError) as context:
            get_input_aligned_bam(wildcards, config, set_type="n")
        self.assertIn("set_type must be None, 'N', 'T', or 'R'", str(context.exception))


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
        with self.assertRaises(AttributeError):
            get_input_haplotagged_bam(wildcards, config)

    def test_missing_sample_wildcard(self):
        wildcards = types.SimpleNamespace(type="T")
        config = dict()
        with self.assertRaises(AttributeError):
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
        self.assertEqual(bam, "snv_indels/whatshap_haplotag/S13_N.haplotagged.bam")
        self.assertEqual(bai, "snv_indels/whatshap_haplotag/S13_N.haplotagged.bam.bai")

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

    def test_with_phaser_in_dict(self):
        """Test phaser in PHASED_BAM_PATHS uses custom path"""
        wildcards = types.SimpleNamespace(sample="S1", type="T")
        config = {"phaser": "whatshap"}
        bam, bai = get_input_haplotagged_bam(
            wildcards,
            config
        )
        self.assertEqual(bam, "snv_indels/whatshap_haplotag/S1_T.haplotagged.bam")
        self.assertEqual(bai, "snv_indels/whatshap_haplotag/S1_T.haplotagged.bam.bai")

    def test_with_phaser_not_in_dict(self):
        """Test phaser not in PHASED_BAM_PATHS uses default pattern"""
        wildcards = types.SimpleNamespace(sample="S1", type="T")
        config = {"phaser": "custom_tool"}
        bam, bai = get_input_haplotagged_bam(
            wildcards,
            config
        )
        self.assertEqual(bam, "snv_indels/custom_tool/S1_T.haplotagged.bam")
        self.assertEqual(bai, "snv_indels/custom_tool/S1_T.haplotagged.bam.bai")

    def test_haplotag_path_takes_precedence_over_phaser(self):
        """Test haplotag_path overrides phaser config"""
        wildcards = types.SimpleNamespace(sample="S1", type="T")
        config = {
            "phaser": "whatshap",
            "haplotag_path": "custom/haplotag/path"
        }
        bam, bai = get_input_haplotagged_bam(
            wildcards,
            config
        )
        self.assertEqual(bam, "custom/haplotag/path/S1_T.haplotagged.bam")
        self.assertEqual(bai, "custom/haplotag/path/S1_T.haplotagged.bam.bai")

    def test_set_type_override_haplotag(self):
        """Test set_type='R' overrides wildcards.type in haplotagged bams"""
        wildcards = types.SimpleNamespace(sample="S15", type="T")
        config = {"phaser": "whatshap"}
        bam, bai = get_input_haplotagged_bam(
            wildcards,
            config,
            set_type="R"
        )
        self.assertEqual(bam, "snv_indels/whatshap_haplotag/S15_R.haplotagged.bam")
        self.assertEqual(bai, "snv_indels/whatshap_haplotag/S15_R.haplotagged.bam.bai")

    def test_set_type_with_suffix(self):
        """Test set_type with suffix"""
        wildcards = types.SimpleNamespace(sample="S16", type="N")
        config = {"phaser": "whatshap"}
        bam, bai = get_input_haplotagged_bam(
            wildcards,
            config,
            set_type="T",
            suffix="phased"
        )
        self.assertEqual(bam, "snv_indels/whatshap_haplotag/S16_T.phased.bam")
        self.assertEqual(bai, "snv_indels/whatshap_haplotag/S16_T.phased.bam.bai")

    def test_set_type_invalid_haplotag(self):
        """Test invalid set_type raises ValueError in haplotagged bam"""
        wildcards = types.SimpleNamespace(sample="S17", type="T")
        config = {"phaser": "whatshap"}
        with self.assertRaises(ValueError) as context:
            get_input_haplotagged_bam(wildcards, config, set_type="X")
        self.assertIn("set_type must be None, 'N', 'T', or 'R'", str(context.exception))
