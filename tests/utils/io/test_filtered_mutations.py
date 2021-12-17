# vim: syntax=python tabstop=4 expandtab
# coding: utf-8

import logging
import os
import shutil
import tempfile
import unittest

from pysam import tabix_index
logger = logging.getLogger(__name__).addHandler(logging.NullHandler())


class TestWp1Reports(unittest.TestCase):
    def setUp(self):

        self.tempdir = tempfile.mkdtemp()

        self.gvcf = os.path.join(self.tempdir, "data.gvcf")
        with open(self.gvcf, 'w', encoding="ascii") as gvcf:
            gvcf.write('##fileformat=VCFv4.2\n')
            gvcf.write('##ALT=<ID=NON_REF,Description="Represents any possible alternative allele not already represented at this location by REF and ALT">\n')  # noqa
            gvcf.write('##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allelic depths for the ref and alt alleles in the order listed">\n')  # noqa
            gvcf.write('##FORMAT=<ID=AF,Number=A,Type=Float,Description="Allele fractions of alternate alleles in the tumor">\n')  # noqa
            gvcf.write('##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Approximate read depth (reads with MQ=255 or with bad mates are filtered)">\n')  # noqa
            gvcf.write('##FORMAT=<ID=F1R2,Number=R,Type=Integer,Description="Count of reads in F1R2 pair orientation supporting each allele">\n')  # noqa
            gvcf.write('##FORMAT=<ID=F2R1,Number=R,Type=Integer,Description="Count of reads in F2R1 pair orientation supporting each allele">\n')  # noqa
            gvcf.write('##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="Genotype Quality">\n')  # noqa
            gvcf.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')  # noqa
            gvcf.write('##FORMAT=<ID=SB,Number=4,Type=Integer,Description="Per-sample component statistics which comprise the Fisher\'s Exact Test to detect strand bias.">\n')  # noqa
            gvcf.write('##FORMAT=<ID=PGT,Number=1,Type=String,Description="Physical phasing haplotype information, describing how the alternate alleles are phased in relation to one another; will always be heterozygous and is not intended to describe called alleles">\n')  # noqa
            gvcf.write('##FORMAT=<ID=PID,Number=1,Type=String,Description="Physical phasing ID information, where each unique ID within a given sample (but not across samples) connects records within a phasing group">\n')  # noqa
            gvcf.write('##FORMAT=<ID=PL,Number=G,Type=Integer,Description="Normalized, Phred-scaled likelihoods for genotypes as defined in the VCF specification">\n')  # noqa
            gvcf.write('##FORMAT=<ID=PS,Number=1,Type=Integer,Description="Phasing set (typically the position of the first variant in the set)">\n')  # noqa
            gvcf.write('##FORMAT=<ID=SB,Number=4,Type=Integer,Description="Per-sample component statistics which comprise the Fisher\'s Exact Test to detect strand bias.">\n')  # noqa
            gvcf.write('##FORMAT=<ID=TLOD,Number=A,Type=Float,Description="Log 10 likelihood ratio score of variant existing versus not existing">\n')  # noqa
            gvcf.write('##GATKCommandLine=<ID=Mutect2,CommandLine="Mutect2 --emit-ref-confidence BP_RESOLUTION --output snv_indels/mutect2_gvcf/UP-VAL-74_T_chr2.gvcf.gz --intervals snv_indels/bed_split/design_bedfile_chr2.bed --input alignment/mark_duplicates/UP-VAL-74_T_chr2.bam --reference /data/ref_genomes/hg19/bwa/BWA_0.7.10_refseq/hg19.with.mt.fasta --f1r2-median-mq 50 --f1r2-min-bq 20 --f1r2-max-depth 200 --genotype-pon-sites false --genotype-germline-sites false --af-of-alleles-not-in-resource -1.0 --mitochondria-mode false --tumor-lod-to-emit 3.0 --initial-tumor-lod 2.0 --pcr-snv-qual 40 --pcr-indel-qual 40 --max-population-af 0.01 --downsampling-stride 1 --callable-depth 10 --max-suspicious-reads-per-alignment-start 0 --normal-lod 2.2 --ignore-itr-artifacts false --gvcf-lod-band -2.5 --gvcf-lod-band -2.0 --gvcf-lod-band -1.5 --gvcf-lod-band -1.0 --gvcf-lod-band -0.5 --gvcf-lod-band 0.0 --gvcf-lod-band 0.5 --gvcf-lod-band 1.0 --minimum-allele-fraction 0.0 --independent-mates false --disable-adaptive-pruning false --kmer-size 10 --kmer-size 25 --dont-increase-kmer-sizes-for-cycles false --allow-non-unique-kmers-in-ref false --num-pruning-samples 1 --min-dangling-branch-length 4 --recover-all-dangling-branches false --max-num-haplotypes-in-population 128 --min-pruning 2 --adaptive-pruning-initial-error-rate 0.001 --pruning-lod-threshold 2.302585092994046 --pruning-seeding-lod-threshold 9.210340371976184 --max-unpruned-variants 100 --linked-de-bruijn-graph false --disable-artificial-haplotype-recovery false --debug-assembly false --debug-graph-transformations false --capture-assembly-failure-bam false --error-correction-log-odds -Infinity --error-correct-reads false --kmer-length-for-read-error-correction 25 --min-observations-for-kmer-to-be-solid 20 --base-quality-score-threshold 18 --pair-hmm-gap-continuation-penalty 10 --pair-hmm-implementation FASTEST_AVAILABLE --pcr-indel-model CONSERVATIVE --phred-scaled-global-read-mismapping-rate 45 --native-pair-hmm-threads 4 --native-pair-hmm-use-double-precision false --bam-writer-type CALLED_HAPLOTYPES --dont-use-soft-clipped-bases false --min-base-quality-score 10 --smith-waterman JAVA --max-mnp-distance 1 --force-call-filtered-alleles false --allele-informative-reads-overlap-margin 2 --min-assembly-region-size 50 --max-assembly-region-size 300 --active-probability-threshold 0.002 --max-prob-propagation-distance 50 --force-active false --assembly-region-padding 100 --padding-around-indels 75 --padding-around-snps 20 --padding-around-strs 75 --max-reads-per-alignment-start 50 --interval-set-rule UNION --interval-padding 0 --interval-exclusion-padding 0 --interval-merging-rule ALL --read-validation-stringency SILENT --seconds-between-progress-updates 10.0 --disable-sequence-dictionary-validation false --create-output-bam-index true --create-output-bam-md5 false --create-output-variant-index true --create-output-variant-md5 false --lenient false --add-output-sam-program-record true --add-output-vcf-command-line true --cloud-prefetch-buffer 40 --cloud-index-prefetch-buffer -1 --disable-bam-index-caching false --sites-only-vcf-output false --help false --version false --showHidden false --verbosity INFO --QUIET false --use-jdk-deflater false --use-jdk-inflater false --gcs-max-retries 20 --gcs-project-for-requester-pays  --disable-tool-default-read-filters false --max-read-length 2147483647 --min-read-length 30 --minimum-mapping-quality 20 --disable-tool-default-annotations false --enable-all-annotations false",Version="4.1.9.0",Date="December 7, 2021 3:57:07 PM UTC">\n')  # noqa
            gvcf.write('##INFO=<ID=AS_SB_TABLE,Number=1,Type=String,Description="Allele-specific forward/reverse read counts for strand bias tests. Includes the reference and alleles separated by |.">\n')  # noqa
            gvcf.write('##INFO=<ID=AS_UNIQ_ALT_READ_COUNT,Number=A,Type=Integer,Description="Number of reads with unique start and mate end positions for each alt at a variant site">\n')  # noqa
            gvcf.write('##INFO=<ID=CONTQ,Number=1,Type=Float,Description="Phred-scaled qualities that alt allele are not due to contamination">\n')  # noqa
            gvcf.write('##INFO=<ID=DP,Number=1,Type=Integer,Description="Approximate read depth; some reads may have been filtered">\n')  # noqa
            gvcf.write('##INFO=<ID=ECNT,Number=1,Type=Integer,Description="Number of events in this haplotype">\n')  # noqa
            gvcf.write('##INFO=<ID=GERMQ,Number=1,Type=Integer,Description="Phred-scaled quality that alt alleles are not germline variants">\n')  # noqa
            gvcf.write('##INFO=<ID=MBQ,Number=R,Type=Integer,Description="median base quality">\n')  # noqa
            gvcf.write('##INFO=<ID=MFRL,Number=R,Type=Integer,Description="median fragment length">\n')  # noqa
            gvcf.write('##INFO=<ID=MMQ,Number=R,Type=Integer,Description="median mapping quality">\n')  # noqa
            gvcf.write('##INFO=<ID=MPOS,Number=A,Type=Integer,Description="median distance from end of read">\n')  # noqa
            gvcf.write('##INFO=<ID=NALOD,Number=A,Type=Float,Description="Negative log 10 odds of artifact in normal with same allele fraction as tumor">\n')  # noqa
            gvcf.write('##INFO=<ID=NCount,Number=1,Type=Integer,Description="Count of N bases in the pileup">\n')  # noqa
            gvcf.write('##INFO=<ID=NLOD,Number=A,Type=Float,Description="Normal log 10 likelihood ratio of diploid het or hom alt genotypes">\n')  # noqa
            gvcf.write('##INFO=<ID=OCM,Number=1,Type=Integer,Description="Number of alt reads whose original alignment doesn\'t match the current contig.">\n')  # noqa
            gvcf.write('##INFO=<ID=PON,Number=0,Type=Flag,Description="site found in panel of normals">\n')  # noqa
            gvcf.write('##INFO=<ID=POPAF,Number=A,Type=Float,Description="negative log 10 population allele frequencies of alt alleles">\n')  # noqa
            gvcf.write('##INFO=<ID=ROQ,Number=1,Type=Float,Description="Phred-scaled qualities that alt allele are not due to read orientation artifact">\n')  # noqa
            gvcf.write('##INFO=<ID=RPA,Number=R,Type=Integer,Description="Number of times tandem repeat unit is repeated, for each allele (including reference)">\n')  # noqa
            gvcf.write('##INFO=<ID=RU,Number=1,Type=String,Description="Tandem repeat unit (bases)">\n')  # noqa
            gvcf.write('##INFO=<ID=SEQQ,Number=1,Type=Integer,Description="Phred-scaled quality that alt alleles are not sequencing errors">\n')  # noqa
            gvcf.write('##INFO=<ID=STR,Number=0,Type=Flag,Description="Variant is a short tandem repeat">\n')  # noqa
            gvcf.write('##INFO=<ID=STRANDQ,Number=1,Type=Integer,Description="Phred-scaled quality of strand bias artifact">\n')  # noqa
            gvcf.write('##INFO=<ID=STRQ,Number=1,Type=Integer,Description="Phred-scaled quality that alt alleles in STRs are not polymerase slippage errors">\n')  # noqa
            gvcf.write('##INFO=<ID=TLOD,Number=A,Type=Float,Description="Log 10 likelihood ratio score of variant existing versus not existing">\n')  # noqa
            gvcf.write("##MutectVersion=2.2\n")
            gvcf.write("##contig=<ID=chr1,length=249250621>\n")
            gvcf.write("##contig=<ID=chr2,length=243199373>\n")
            gvcf.write("##contig=<ID=chr3,length=198022430>\n")
            gvcf.write("##contig=<ID=chr4,length=191154276>\n")
            gvcf.write("##contig=<ID=chr5,length=180915260>\n")
            gvcf.write("##contig=<ID=chr6,length=171115067>\n")
            gvcf.write("##contig=<ID=chr7,length=159138663>\n")
            gvcf.write("##contig=<ID=chr8,length=146364022>\n")
            gvcf.write("##contig=<ID=chr9,length=141213431>\n")
            gvcf.write("##contig=<ID=chr10,length=135534747>\n")
            gvcf.write("##contig=<ID=chr11,length=135006516>\n")
            gvcf.write("##contig=<ID=chr12,length=133851895>\n")
            gvcf.write("##contig=<ID=chr13,length=115169878>\n")
            gvcf.write("##contig=<ID=chr14,length=107349540>\n")
            gvcf.write("##contig=<ID=chr15,length=102531392>\n")
            gvcf.write("##contig=<ID=chr16,length=90354753>\n")
            gvcf.write("##contig=<ID=chr17,length=81195210>\n")
            gvcf.write("##contig=<ID=chr18,length=78077248>\n")
            gvcf.write("##contig=<ID=chr19,length=59128983>\n")
            gvcf.write("##contig=<ID=chr20,length=63025520>\n")
            gvcf.write("##contig=<ID=chr21,length=48129895>\n")
            gvcf.write("##contig=<ID=chr22,length=51304566>\n")
            gvcf.write("##contig=<ID=chrX,length=155270560>\n")
            gvcf.write("##contig=<ID=chrY,length=59373566>\n")
            gvcf.write("##contig=<ID=chrM,length=16571>\n")
            gvcf.write("##filtering_status=Warning: unfiltered Mutect 2 calls.  Please run FilterMutectCalls to remove false positives.\n")  # noqa
            gvcf.write("##source=Mutect2\n")
            gvcf.write("##tumor_sample=sample1\n")
            gvcf.write(r"#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	sample1")
            gvcf.write("\n")
            gvcf.write(r"chr2	29445270	.	A	C,<NON_REF>	.	.	AS_SB_TABLE=449,168|2,2|0,0;DP=643;ECNT=33;MBQ=36,14,0;MFRL=193,210,0;MMQ=60,60,60;MPOS=36,50;POPAF=7.30,7.30;TLOD=-2.431e+00,-2.428e+00	GT:AD:AF:DP:F1R2:F2R1:SB	0/1/2:617,4,0:1.895e-03,1.858e-03:621:278,0,0:304,0,0:449,168,2,2")  # noqa
            gvcf.write("\n")
            gvcf.write(r"chr2	29445271	.	G	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:620,0:620:-2.793e+00")
            gvcf.write("\n")
            gvcf.write(r"chr2	29445272	.	C	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:219,2:221:-4.333e+00")
            gvcf.write("\n")
            gvcf.write(r"chr2	29445273	.	GT	TG,<NON_REF>	.	.	AS_SB_TABLE=460,168|0,0|0,0;DP=628;ECNT=33;MBQ=32,0,0;MFRL=193,0,0;MMQ=60,60,60;MPOS=50,50;POPAF=7.30,7.30;TLOD=-2.432e+00,-2.432e+00	GT:AD:AF:DP:F1R2:F2R1:PGT:PID:PS:SB	0|1|2:628,0,0:1.844e-03,1.844e-03:628:291,0,0:309,0,0:0|1:29445255_G_C:29445255:460,168,0,0")  # noqa
            gvcf.write("\n")
            gvcf.write(r"chr2	29445274	.	T	G,<NON_REF>	.	.	AS_SB_TABLE=453,162|2,1|0,0;DP=626;ECNT=33;MBQ=32,14,0;MFRL=193,195,0;MMQ=60,60,60;MPOS=47,50;POPAF=7.30,7.30;TLOD=-2.246e+00,-2.255e+00	GT:AD:AF:DP:F1R2:F2R1:SB	0/1/2:615,3,0:1.911e-03,1.851e-03:618:280,0,0:297,0,0:453,162,2,1")  # noqa
            gvcf.write("\n")
            gvcf.write(r"chr2	29445275	.	C	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:605,3:608:-5.996e+00")
            gvcf.write("\n")
            gvcf.write(r"chr2	29445276	.	T	G,<NON_REF>	.	.	AS_SB_TABLE=458,163|0,0|0,0;DP=624;ECNT=33;MBQ=36,0,0;MFRL=193,0,0;MMQ=60,60,60;MPOS=50,50;POPAF=7.30,7.30;TLOD=-2.430e+00,-2.430e+00	GT:AD:AF:DP:F1R2:F2R1:SB	0/1/2:621,0,0:1.860e-03,1.860e-03:621:282,0,0:291,0,0:458,163,0,0")  # noqa
            gvcf.write("\n")
            gvcf.write(r"chr2	29445277	.	G	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:179,3:182:-4.683e+00")
            gvcf.write("\n")
            gvcf.write(r"chr2	29445278	.	G	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:145,5:550:-1.031e+01")
            gvcf.write("\n")
            gvcf.write(r"chr2	29445279	.	G	C,<NON_REF>	.	.	AS_SB_TABLE=451,143|0,0|0,0;DP=594;ECNT=33;MBQ=36,0,0;MFRL=199,0,0;MMQ=60,60,60;MPOS=50,50;POPAF=7.30,7.30;TLOD=-2.416e+00,-2.416e+00	GT:AD:AF:DP:F1R2:F2R1:SB	0/1/2:594,0,0:1.916e-03,1.916e-03:594:250,0,0:271,0,0:451,143,0,0")  # noqa
            gvcf.write("\n")
            gvcf.write(r"chr2	29445280	.	C	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:536,3:539:-3.197e+00")
            gvcf.write("\n")
            gvcf.write(r"chr2	29445281	.	A	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:524,2:526:-7.281e+00")
            gvcf.write("\n")
            gvcf.write(r"chr2	29445282	.	G	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:519,1:520:-5.233e+00")
            gvcf.write("\n")
            gvcf.write(r"chr8	145738765	.	C	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:1615,1:1616:-6.047e+00")
            gvcf.write("\n")
            gvcf.write(r"chr8	145738766	.	C	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:1616,3:1619:-1.159e+01")
            gvcf.write("\n")
            gvcf.write(r"chr8	145738767	.	CG	C,<NON_REF>	.	.	AS_SB_TABLE=40,6|787,762|0,0;DP=1687;ECNT=41;MBQ=20,20,0;MFRL=169,152,0;MMQ=60,60,60;MPOS=31,50;POPAF=7.30,7.30;TLOD=3010.36,-2.692e+00	GT:AD:AF:DP:F1R2:F2R1:SB	0/1/2:46,1549,0:0.998,9.666e-04:1595:24,753,0:16,761,0:40,6,787,762")  # noqa
            gvcf.write("\n")
            gvcf.write(r"chr8	145738768	.	G	C,<NON_REF>	.	.	AS_SB_TABLE=372,701|428,46|0,0;DP=1680;ECNT=41;MBQ=14,20,0;MFRL=142,162,0;MMQ=60,60,60;MPOS=30,50;POPAF=7.30,7.30;TLOD=-2.582e+00,-2.546e+00	GT:AD:AF:DP:F1R2:F2R1:SB	0/1/2:1073,474,0:0.333,2.407e-03:1547:0,22,0:0,16,0:372,701,428,46")  # noqa
            gvcf.write("\n")
            gvcf.write(r"chr8	145738769	.	G	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:1636,8:1644:-1.467e+01")
            gvcf.write("\n")
            gvcf.write(r"chr8	145738770	.	C	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:1663,4:1667:-9.366e+00")
            gvcf.write("\n")
            gvcf.write(r"chr8	145738771	.	A	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:1681,4:1685:-1.401e+01")
            gvcf.write("\n")
            gvcf.write(r"chr8	145738772	.	A	C,<NON_REF>	.	.	AS_SB_TABLE=865,812|8,4|0,0;DP=1717;ECNT=41;MBQ=20,14,0;MFRL=152,202,0;MMQ=60,60,60;MPOS=20,50;POPAF=7.30,7.30;TLOD=-2.740e+00,-2.730e+00	GT:AD:AF:DP:F1R2:F2R1:SB	0/1/2:1677,12,0:9.536e-04,9.240e-04:1689:705,2,0:745,0,0:865,812,8,4")  # noqa
            gvcf.write("\n")
            gvcf.write(r"chr8	145738773	.	C	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:1939,1:1940:-6.511e+00")
            gvcf.write("\n")
            gvcf.write(r"chr8	145738774	.	T	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:1932,8:1940:-2.085e+01")
            gvcf.write("\n")
            gvcf.write(r"chr8	145738775	.	G	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:1961,2:1963:-3.168e+00")
            gvcf.write("\n")
            gvcf.write(r"chr8	145738777	.	C	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:1958,6:1964:-1.518e+01")
            gvcf.write("\n")
            gvcf.write(r"chr8	145738778	.	C	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:1952,11:1963:-2.410e+01")
            gvcf.write("\n")
            gvcf.write(r"chr8	145738779	.	C	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:1951,7:1958:-1.404e+01")
            gvcf.write("\n")
            gvcf.write(r"chr8	145738780	.	T	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:1951,6:1957:-9.717e+00")
            gvcf.write("\n")
            gvcf.write(r"chr8	145738781	.	G	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:1958,5:1963:-1.577e+01")
            gvcf.write("\n")
            gvcf.write(r"chr8	145738782	.	C	<NON_REF>	.	.	.	GT:AD:DP:TLOD	0/0:1957,2:1959:-5.811e+00")

        tabix_index(self.gvcf, preset="vcf")

        self.multibp = os.path.join(self.tempdir, "multibp")
        with open(os.path.join(self.tempdir, "multibp"), 'w') as multibp:
            multibp.write("NC_000007.13\t55242465\t55242479\tGGAATTAAGAGAAGC\t-\tEGFR\tc.2235_2249del\tp.E746_A750del\tNM_005228.3\n")  # noqa

        self.hotspot = os.path.join(self.tempdir, "hotspot")
        with open(self.hotspot, 'w') as hotspots:
            hotspots.write("#Chr\tStart\tEnd\tGene\tCDS_mutation_syntax\tAA_mutation_syntax\tReport\tcomment\tExon\tAccession_number\n")  # noqa
            hotspots.write("NC_000002.11\t29445271\t29445271\tALK\tc.G3467\tp.C1156\thotspot\tresistance_mutation\texon22\tNM_004304\n")  # noqa
            hotspots.write("NC_000002.11\t29445271\t29445281\tALK\tc.G3467\tp.C1156\tregion_all\t-\texon22\tNM_004304\n")
            hotspots.write("NC_000007.13\t140498361\t140498361\tEGFR\tc.G2236\tp.E746\thotspot\t-\texon19\tNM_005228\n")
            hotspots.write("NC_000007.13\t140453136\t140453136\tBRAF\tc.T1799\tp.V600\thotspot\t-\texon15\tNM_004333\n")
            hotspots.write("NC_000007.13\t116412043\t116412043\tMET\tc.G3082\tp.D1028\thotspot\t-\texon14\tNM_001127500\n")
            hotspots.write("NC_000008.11\t145738765\t145738779\t-\t-\t-\tregion_all\t-\texon1\t-\n")
            hotspots.write("NC_000008.11\t145742510\t145742524\t-\t-\t-\tregion\t-\texon1\t-\n")

        self.vcf_vep = os.path.join(self.tempdir, "vcf_vep.vcf")
        with open(self.vcf_vep, "w", encoding="ascii") as vcf:
            vcf.write("##fileformat=VCFv4.2\n")
            vcf.write("##reference=/data/ref_genomes/hg19/bwa/BWA_0.7.10_refseq/hg19.with.mt.fast\n")
            vcf.write("##contig=<ID=chr1,length=249250621>\n")
            vcf.write("##contig=<ID=chr2,length=243199373>\n")
            vcf.write("##contig=<ID=chr3,length=198022430>\n")
            vcf.write("##contig=<ID=chr4,length=191154276>\n")
            vcf.write("##contig=<ID=chr5,length=180915260>\n")
            vcf.write("##contig=<ID=chr6,length=171115067>\n")
            vcf.write("##contig=<ID=chr7,length=159138663>\n")
            vcf.write("##contig=<ID=chr8,length=146364022>\n")
            vcf.write("##contig=<ID=chr9,length=141213431>\n")
            vcf.write("##contig=<ID=chr10,length=135534747>\n")
            vcf.write("##contig=<ID=chr11,length=135006516>\n")
            vcf.write("##contig=<ID=chr12,length=133851895>\n")
            vcf.write("##contig=<ID=chr13,length=115169878>\n")
            vcf.write("##contig=<ID=chr14,length=107349540>\n")
            vcf.write("##contig=<ID=chr15,length=102531392>\n")
            vcf.write("##contig=<ID=chr16,length=90354753>\n")
            vcf.write("##contig=<ID=chr17,length=81195210>\n")
            vcf.write("##contig=<ID=chr18,length=78077248>\n")
            vcf.write("##contig=<ID=chr19,length=59128983>\n")
            vcf.write("##contig=<ID=chr20,length=63025520>\n")
            vcf.write("##contig=<ID=chr21,length=48129895>\n")
            vcf.write("##contig=<ID=chr22,length=51304566>\n")
            vcf.write("##contig=<ID=chrX,length=155270560>\n")
            vcf.write("##contig=<ID=chrY,length=59373566>\n")
            vcf.write('##contig=<ID=chrM,length=16571>\n')
            vcf.write('##INFO=<ID=CALLERS,Number=.,Type=String,Description="Individual caller support">\n')
            vcf.write('##INFO=<ID=MQ,Number=1,Type=Float,Description="Mean Mapping Quality">\n')
            vcf.write('##FORMAT=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">\n')
            vcf.write('##INFO=<ID=ADJAF,Number=1,Type=Float,Description="Adjusted AF for indels due to local realignment">\n')
            vcf.write('##INFO=<ID=BIAS,Number=1,Type=String,Description="Strand Bias Info">\n')
            vcf.write('##INFO=<ID=BIAS,Number=1,Type=String,Description="Strand Bias Info">\n')
            vcf.write('##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">\n')
            vcf.write('##INFO=<ID=DUPRATE,Number=1,Type=Float,Description="Duplication rate in fraction">\n')
            vcf.write('##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">\n')
            vcf.write('##INFO=<ID=HIAF,Number=1,Type=Float,Description="Allele frequency using only high quality bases">\n')
            vcf.write('##INFO=<ID=HICNT,Number=1,Type=Integer,Description="High quality variant reads">\n')
            vcf.write('##INFO=<ID=HICOV,Number=1,Type=Integer,Description="High quality total reads">\n')
            vcf.write('##INFO=<ID=LSEQ,Number=1,Type=String,Description="5\' flanking seq">\n')
            vcf.write('##INFO=<ID=MMQ,Number=R,Type=Integer,Description="median mapping quality">\n')
            vcf.write('##INFO=<ID=MSI,Number=1,Type=Float,Description="MicroSatellite. > 1 indicates MSI">\n')
            vcf.write('##INFO=<ID=MSILEN,Number=1,Type=Float,Description="MicroSatellite unit length in bp">\n')
            vcf.write('##INFO=<ID=NM,Number=1,Type=Float,Description="Mean mismatches in reads">\n')
            vcf.write('##INFO=<ID=ODDRATIO,Number=1,Type=Float,Description="Strand Bias Odds ratio">\n')
            vcf.write('##INFO=<ID=PMEAN,Number=1,Type=Float,Description="Mean position in reads">\n')
            vcf.write('##INFO=<ID=PSTD,Number=1,Type=Float,Description="Position STD in reads">\n')
            vcf.write('##INFO=<ID=QSTD,Number=1,Type=Float,Description="Quality score STD in reads">\n')
            vcf.write('##INFO=<ID=QUAL,Number=1,Type=Float,Description="Mean quality score in reads">\n')
            vcf.write('##INFO=<ID=REFBIAS,Number=1,Type=String,Description="Reference depth by strand">\n')
            vcf.write('##INFO=<ID=RSEQ,Number=1,Type=String,Description="3\' flanking seq">\n')
            vcf.write('##INFO=<ID=SAMPLE,Number=1,Type=String,Description="Sample name (with whitespace translated to underscores)">\n')  # noqa
            vcf.write('##INFO=<ID=SBF,Number=1,Type=Float,Description="Strand Bias Fisher p-value">\n')
            vcf.write('##INFO=<ID=SHIFT3,Number=1,Type=Integer,Description="No. of bases to be shifted to 3 prime for deletions due to alternative alignment">\n')  # noqa
            vcf.write('##INFO=<ID=SN,Number=1,Type=Float,Description="Signal to noise">\n')
            vcf.write('##INFO=<ID=SPANPAIR,Number=1,Type=Integer,Description="No. of pairs supporting SV">\n')
            vcf.write('##INFO=<ID=SPLITREAD,Number=1,Type=Integer,Description="No. of split reads supporting SV">\n')
            vcf.write('##INFO=<ID=TYPE,Number=1,Type=String,Description="Variant Type: SNV Insertion Deletion Complex">\n')
            vcf.write('##INFO=<ID=VARBIAS,Number=1,Type=String,Description="Variant depth by strand">\n')
            vcf.write('##INFO=<ID=VD,Number=1,Type=Integer,Description="Variant Depth">\n')
            vcf.write('##INFO=<ID=AS_SB_TABLE,Number=1,Type=String,Description="Allele-specific forward/reverse read counts for strand bias tests. Includes the reference and alleles separated by |.">\n')  # noqa
            vcf.write('##INFO=<ID=ECNT,Number=1,Type=Integer,Description="Number of events in this haplotype">\n')
            vcf.write('##INFO=<ID=MBQ,Number=R,Type=Integer,Description="median base quality">\n')
            vcf.write('##INFO=<ID=MFRL,Number=R,Type=Integer,Description="median fragment length">\n')
            vcf.write('##INFO=<ID=MPOS,Number=A,Type=Integer,Description="median distance from end of read">\n')
            vcf.write('##INFO=<ID=OLD_MULTIALLELIC,Number=1,Type=String,Description="Original chr:pos:ref:alt encoding">\n')
            vcf.write('##INFO=<ID=OLD_VARIANT,Number=.,Type=String,Description="Original chr:pos:ref:alt encoding">\n')
            vcf.write('##INFO=<ID=POPAF,Number=A,Type=Float,Description="negative log 10 population allele frequencies of alt alleles">\n')  # noqa
            vcf.write('##INFO=<ID=TLOD,Number=A,Type=Float,Description="Log 10 likelihood ratio score of variant existing versus not existing">\n')  # noqa
            vcf.write('##FORMAT=<ID=AD,Number=.,Type=Integer,Description="Allelic depths for the ref and alt alleles in the order listed">\n')  # noqa
            vcf.write('##FORMAT=<ID=ALD,Number=2,Type=Integer,Description="Variant forward, reverse reads">\n')
            vcf.write('##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Total Depth">\n')
            vcf.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')
            vcf.write('##FORMAT=<ID=SB,Number=4,Type=Integer,Description="Per-sample component statistics which comprise the Fisher\'s Exact Test to detect strand bias.">\n')  # noqa
            vcf.write('##FORMAT=<ID=RD,Number=2,Type=Integer,Description="Reference forward, reverse reads">\n')
            vcf.write('##FORMAT=<ID=VD,Number=1,Type=Integer,Description="Variant Depth">\n')
            vcf.write('##FORMAT=<ID=F1R2,Number=R,Type=Integer,Description="Count of reads in F1R2 pair orientation supporting each allele">\n')  # noqa
            vcf.write('##FORMAT=<ID=F2R1,Number=R,Type=Integer,Description="Count of reads in F2R1 pair orientation supporting each allele">\n')  # noqa
            vcf.write("##VEP=\"v99\" time=\"2021-10-28 13:27:59\" cache=\"/data/ref_genomes/VEP/homo_sapiens_refseq/99_GRCh37\" ensembl=99.d3e7d31 ensembl-variation=99.642e1cd ensembl-funcgen=99.0832337 ensembl-io=99.441b05b 1000genomes=\"phase3\" COSMIC=\"86\" ClinVar=\"201810\" ESP=\"20141103\" HGMD-PUBLIC=\"20174\" assembly=\"GRCh37.p13\" dbSNP=\"151\" gencode=\"GENCODE 19\" genebuild=\"2011-04\" gnomAD=\"r2.1\" polyphen=\"2.2.2\" refseq=\"01_2015\" regbuild=\"1.0\" sift=\"sift5.2.2\"\n")  # noqa
            vcf.write("##INFO=<ID=CSQ,Number=.,Type=String,Description=\"Consequence annotations from Ensembl VEP. Format: Allele|Consequence|IMPACT|SYMBOL|Gene|Feature_type|Feature|BIOTYPE|EXON|INTRON|HGVSc|HGVSp|cDNA_position|CDS_position|Protein_position|Amino_acids|Codons|Existing_variation|DISTANCE|STRAND|FLAGS|VARIANT_CLASS|SYMBOL_SOURCE|HGNC_ID|CANONICAL|TSL|APPRIS|CCDS|ENSP|SWISSPROT|TREMBL|UNIPARC|REFSEQ_MATCH|GIVEN_REF|USED_REF|BAM_EDIT|GENE_PHENO|SIFT|PolyPhen|DOMAINS|HGVS_OFFSET|AF|AFR_AF|AMR_AF|EAS_AF|EUR_AF|SAS_AF|gnomAD_AF|gnomAD_AFR_AF|gnomAD_AMR_AF|gnomAD_ASJ_AF|gnomAD_EAS_AF|gnomAD_FIN_AF|gnomAD_NFE_AF|gnomAD_OTH_AF|gnomAD_SAS_AF|MAX_AF|MAX_AF_POPS|CLIN_SIG|SOMATIC|PHENO|PUBMED|MOTIF_NAME|MOTIF_POS|HIGH_INF_POS|MOTIF_SCORE_CHANGE\">\n")  # noqa
            vcf.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsample1\n")
            vcf.write(r"chr2	29445271	.	G	A	72	PASS	ADJAF=0;AF=0.011;BIAS=2:2;CALLERS=vardict;DP=363;DUPRATE=0;HIAF=0.0117;HICNT=4;HICOV=342;LSEQ=TTCAGAGCACACTTCAGGCA;MQ=60;MSI=1;MSILEN=1;NM=1;ODDRATIO=1.31511;PMEAN=14.5;PSTD=1;QSTD=0;QUAL=36;REFBIAS=204:155;RSEQ=CGTCTGGGCAGAGAAGGGGA;SAMPLE=UP-VAL-78_T;SBF=1;SHIFT3=2;SN=8;SPANPAIR=0;SPLITREAD=0;TYPE=SNV;VARBIAS=2:2;VD=4;CSQ=A|synonymous_variant|LOW|ALK|238|Transcript|NM_004304.4|protein_coding|22/29||NM_004304.4:c.3454C>T|NP_004295.2:p.Leu1152%3D|4406|3454|1152|L|Ctg/Ttg|||-1||SNV|EntrezGene||YES||||NP_004295.2|||||G|G|OK||||||||||||||||||||||||||||||	GT:DP:VD:AD:AF:RD:ALD	0/1:363:4:359,4:0.011:204,155:2,2")  # noqa
            vcf.write("\n")
            vcf.write(r"chr2	29445282	.	G	A	45	PASS	ADJAF=0;AF=0.0104;BIAS=2:2;CALLERS=vardict;DP=288;DUPRATE=0;HIAF=0.0085;HICNT=2;HICOV=236;LSEQ=CTTCAGGCAGCGTCTGGGCA;MQ=60;MSI=2;MSILEN=2;NM=1.3;ODDRATIO=1.42001;PMEAN=9;PSTD=1;QSTD=1;QUAL=28.7;REFBIAS=166:118;RSEQ=AGAAGGGGAGGGTGGGGAGG;SAMPLE=UP-VAL-78_T;SBF=1;SHIFT3=0;SN=2;SPANPAIR=0;SPLITREAD=0;TYPE=SNV;VARBIAS=2:1;VD=3;CSQ=A|splice_region_variant&intron_variant|LOW|ALK|238|Transcript|NM_004304.4|protein_coding||21/28|NM_004304.4:c.3451-8C>T|||||||rs1305183150||-1||SNV|EntrezGene||YES||||NP_004295.2|||||G|G|OK||||||||||||3.979e-06|0|2.892e-05|0|0|0|0|0|0|2.892e-05|gnomAD_AMR||||||||	GT:DP:VD:AD:AF:RD:ALD	0/1:288:3:284,3:0.0104:166,118:2,1")  # noqa
            vcf.write("\n")
            vcf.write(r"chr7	140498359	.	CTTT	C	.	PASS	AF=0.095;AS_SB_TABLE=7,20|0,4|4,8|0,2;CALLERS=mutect2;DP=72;ECNT=1;MBQ=20,24;MFRL=233,291;MMQ=60,60;MPOS=17;OLD_MULTIALLELIC=chr7:140498359:CTTT/C/CTT/CGTTTTTTTT;POPAF=7.3;TLOD=3.69;CSQ=-|intron_variant|MODIFIER|BRAF|673|Transcript|XM_005250045.1|protein_coding||7/18|XM_005250045.1:c.980+1800_980+1802del|||||||rs1274460177||-1||deletion|EntrezGene||YES||||XP_005250102.1|||||TTT|TTT|||||||||||||||||||||||||||||||	GT:AD:AF:DP:F1R2:F2R1:SB	0/1/./.:27,4:0.095:45:7,0:10,3:7,20,4,14")  # noqa
            vcf.write("\n")
            vcf.write(r"chr8	145738768	.	G	C	154	PASS	ADJAF=0;AF=0.0333;BIAS=2:2;CALLERS=vardict;DP=812;DUPRATE=0;HIAF=0.033;HICNT=26;HICOV=788;LSEQ=CACCGTGGCCACCACCACCC;MQ=60;MSI=2;MSILEN=1;NM=2.6;ODDRATIO=1.94917;PMEAN=33.4;PSTD=1;QSTD=1;QUAL=32.4;REFBIAS=4:1;RSEQ=GCAACTGGCCCTGCATGAAG;SAMPLE=UP-VAL-79_T;SBF=0.51196;SHIFT3=0;SN=26;SPANPAIR=0;SPLITREAD=0;TYPE=SNV;VARBIAS=24:3;VD=27;CSQ=C|upstream_gene_variant|MODIFIER|LRRC14|9684|Transcript|NM_001272036.1|protein_coding||||||||||rs199605511|4581|1||SNV|EntrezGene||YES||||NP_001258965.1|||||G|G|OK||||||||||||1.672e-05|0|0|0|0|0|2.76e-05|0|3.281e-05|3.281e-05|gnomAD_SAS||||||||	GT:DP:VD:AD:AF:RD:ALD	0/1:812:27:5,27:0.0333:4,1:24,3")  # noqa
            vcf.write("\n")
            vcf.write(r"chr8	145742514	.	A	G	335	PASS	ADJAF=0.0166;AF=0.9941;BIAS=0:2;CALLERS=vardict,mutect2;DP=844;DUPRATE=0;HIAF=0.9976;HICNT=817;HICOV=819;LSEQ=GCGGCTCCGCCCTGGCGTAG;MQ=60;MSI=1;MSILEN=1;NM=1.6;ODDRATIO=0;PMEAN=35.9;PSTD=1;QSTD=1;QUAL=34.5;REFBIAS=0:0;RSEQ=CTGTGGACTCTTGGTCGCAG;SAMPLE=UP-VAL-79_T;SBF=1;SHIFT3=0;SN=37.136;SPANPAIR=0;SPLITREAD=0;TYPE=SNV;VARBIAS=410:429;VD=839;CSQ=G|synonymous_variant|LOW|RECQL4|9401|Transcript|NM_004260.3|protein_coding|4/21||NM_004260.3:c.274T>C|NP_004251.3:p.Pro92%3D|316|274|92|P|Cct/Cct|rs2721190||-1||SNV|EntrezGene||YES||||NP_004251.3|||||A|G|OK||||||0.9433|0.9781|0.9222|0.8065|0.998|0.9959|0.9697|0.9819|0.9021|1|0.803|0.9968|0.9994|0.9809|0.9985|1|gnomAD_ASJ|||1|24728327||||	GT:DP:VD:AD:AF:RD:ALD	1/1:844:839:0,839:0.9941:0,0:410,429")  # noqa
        tabix_index(self.vcf_vep, preset="vcf")

        self.reference = os.path.join(self.tempdir, "reference_info")
        with open(self.reference, 'w') as reference:
            reference.write("#Chr name\tNC\tID\tLength\n")
            reference.write("chr1\tNC_000001.10\tchr1#NC_000001.10#1#249250621#-1\t249250621\n")
            reference.write("chr2\tNC_000002.11\tchr2#NC_000002.10#1#242951149#-1\t242951149\n")
            reference.write("chr3\tNC_000003.10\tchr3#NC_000003.10#1#199501827#-1\t199501827\n")
            reference.write("chr4\tNC_000004.10\tchr4#NC_000004.10#1#191273063#-1\t191273063\n")
            reference.write("chr5\tNC_000005.8\tchr5#NC_000005.8#1#180857866#-1\t180857866\n")
            reference.write("chr6\tNC_000006.10\tchr6#NC_000006.10#1#170899992#-1\t170899992\n")
            reference.write("chr7\tNC_000007.13\tchr7#NC_000007.13#1#159138663#-1\t159138663\n")
            reference.write("chr8\tNC_000008.11\tchr7#NC_000007.13#1#159138663#-1\t159138663\n")
            reference.write("chr12\tNC_000012.11\tchr12#NC_000012.11#1#133851895#-1\t133851895\n")
            reference.write("chr17\tNC_000017.10\tchr17#NC_000017.10#1#81195210#-1\t81195210")

    def tearDown(self):
        # delete fixtures
        shutil.rmtree(self.tempdir)

    def test_get_read_level(self):
        from hydra_genetics.utils.io.utils import get_read_level
        levels = [(300, "ok", "yes"), (30, "low", "yes"), (0, "low", "not analyzable")]
        self.assertEqual(get_read_level(levels, 300), ("ok", "yes"))
        self.assertEqual(get_read_level(levels, 200), ("low", "yes"))
        self.assertEqual(get_read_level(levels, 30), ("low", "yes"))
        self.assertEqual(get_read_level(levels, 15), ("low", "not analyzable"))
        self.assertEqual(get_read_level(levels, 0), ("low", "not analyzable"))
        self.assertEqual(get_read_level(levels, -15), ("-", "zero"))
        self.assertEqual(get_read_level(levels, "-"), ("-", "zero"))

    def test_filtered_mutation_creation_annovar(self):
        from hydra_genetics.utils.io.filtered_mutations import generate_filtered_mutations
        levels = [(300, "ok", "yes"), (30, "low", "yes"), (0, "low", "not analyzable")]

        self.maxDiff = 10000

        report = os.path.join(self.tempdir, "filtered.report")
        generate_filtered_mutations("sample1",
                                    "variant_caller",
                                    report,
                                    levels,
                                    self.hotspot,
                                    self.vcf_vep + ".gz",
                                    self.gvcf + ".gz",
                                    self.reference)
        self.maxDiff = 10000

        # Variants
        # chr2	29445271	.	G	A  (1)
        # chr2	29445282	.	G	A  (other)
        # chr7	140498359	.	CTTT	C (3)
        # chr8	145738768	.	G	C (6)
        # chr8	145742514	.	A	G
        #
        # Hotspot
        # 1 - NC_000002.11  29445271    29445271    hotspot
        # 2 - NC_000002.11  29445271    29445281    region_all
        # 3 - NC_000007.13  140498361   140498361   hotspot  # Should this one be printed eventhough a indel overlaps it?
        # 4 - NC_000007.13  140453136   140453136   hotspot
        # 5 - NC_000007.13  116412043   116412043   hotspot
        # 6 - NC_000008.11  145738765    145738779    region_all
        # 7 - NC_000008.11  145742510    145742524    region
        #
        with open(report, 'r') as report_result:
            head = report_result.readline()
            self.assertEqual(head.rstrip(), "\t".join(["sample", "chr", "start", "end", "report", 'gvcf_depth']))
            result = report_result.readlines()
            self.assertEqual(len(result), 11)
            self.assertEqual(result[0].rstrip(), "sample1	NC_000002.11	29445270	29445270	G	A	1-hotspot	620	359	4")
            self.assertEqual(result[1].rstrip(), "sample1	NC_000007.13	140498358	140498361	CTTT	C	2-indel	0	27	4")
            self.assertEqual(result[2].rstrip(), "sample1	NC_000007.13	140498361	140498361	-	-	hotspot	0	-	-")
            self.assertEqual(result[3].rstrip(), "sample1	NC_000007.13	140453136	140453136	-	-	hotspot	0	-	-")
            self.assertEqual(result[4].rstrip(), "sample1	NC_000007.13	116412043	116412043	-	-	hotspot	0	-	-")
            self.assertEqual(result[5].rstrip(), "sample1	NC_000002.11	29445272	29445272	-	-	region_all	221	-	-")
            self.assertEqual(result[6].rstrip(), "sample1	NC_000002.11	29445277	29445277	-	-	region_all	182	-	-")
            self.assertEqual(result[7].rstrip(), "sample1	NC_000008.11	145738767	145738767	G	C	3-check	1571	5	27")
            self.assertEqual(result[8].rstrip(), "sample1	NC_000008.11	145738776	145738776	-	-	region_all	0	-	-")
            self.assertEqual(result[9].rstrip(), "sample1	NC_000008.11	145742513	145742513	A	G	3-check	0	0	839")
            self.assertEqual(result[10].rstrip(), "sample1	NC_000002.11	29445281	29445281	G	A	4-other	520	284	3")

        report = os.path.join(self.tempdir, "filtered.report")
        generate_filtered_mutations("sample1",
                                    "variant_caller",
                                    report,
                                    levels,
                                    self.hotspot,
                                    self.vcf_vep + ".gz",
                                    self.gvcf + ".gz",
                                    self.reference,
                                    "tests/utils/files/report_columns_vep.yaml")
        with open(report, 'r') as report_result:
            head = report_result.readline()
            self.assertEqual(head.rstrip(), "\t".join(["sample", "chr", "start", "end", "report", 'gvcf_depth', 'Analyzable', 'Min_read_depth300', 'Gene', 'Variant_type', 'Consequence', 'Callers', 'Comment']))  # noqa
            result = report_result.readlines()
            self.assertEqual(len(result), 11)
            self.assertEqual(result[0].rstrip(), "sample1	NC_000002.11	29445270	29445270	G	A	1-hotspot	620	359	4	yes	ok	ALK	protein_coding	synonymous_variant	vardict	resistance_mutation")  # noqa
            self.assertEqual(result[1].rstrip(), "sample1	NC_000007.13	140498358	140498361	CTTT	C	2-indel	0	27	4	not analyzable	low	BRAF	protein_coding	intron_variant	mutect2	-")  # noqa
            self.assertEqual(result[2].rstrip(), "sample1	NC_000007.13	140498361	140498361	-	-	hotspot	0	-	-	not analyzable	low	-	-	-	-	-")   # noqa
            self.assertEqual(result[3].rstrip(), "sample1	NC_000007.13	140453136	140453136	-	-	hotspot	0	-	-	not analyzable	low	-	-	-	-	-")  # noqa
            self.assertEqual(result[4].rstrip(), "sample1	NC_000007.13	116412043	116412043	-	-	hotspot	0	-	-	not analyzable	low	-	-	-	-	-")  # noqa
            self.assertEqual(result[5].rstrip(), "sample1	NC_000002.11	29445272	29445272	-	-	region_all	221	-	-	yes	low	-	-	-	-	-")  # noqa
            self.assertEqual(result[6].rstrip(), "sample1	NC_000002.11	29445277	29445277	-	-	region_all	182	-	-	yes	low	-	-	-	-	-")  # noqa
            self.assertEqual(result[7].rstrip(), "sample1	NC_000008.11	145738767	145738767	G	C	3-check	1571	5	27	yes	ok	LRRC14	protein_coding	upstream_gene_variant	vardict	-")  # noqa
            self.assertEqual(result[8].rstrip(), "sample1	NC_000008.11	145738776	145738776	-	-	region_all	0	-	-	not analyzable	low	-	-	-	-	-")  # noqa
            self.assertEqual(result[9].rstrip(), "sample1	NC_000008.11	145742513	145742513	A	G	3-check	0	0	839	not analyzable	low	RECQL4	protein_coding	synonymous_variant	vardict,mutect2	-")  # noqa
            self.assertEqual(result[10].rstrip(), "sample1	NC_000002.11	29445281	29445281	G	A	4-other	520	284	3	yes	ok	ALK	protein_coding	splice_region_variant&intron_variant	vardict	-")  # noqa


if __name__ == '__main__':
    import logging
    import sys
    logging.basicConfig(level=logging.CRITICAL, stream=sys.stdout, format='%(message)s')
    unittest.main()