# Changelog

## [3.1.1](https://github.com/hydra-genetics/hydra-genetics/compare/v3.1.0...v3.1.1) (2024-11-05)


### Bug Fixes

* Correct reading VEP header from vcf ([76c3ed8](https://github.com/hydra-genetics/hydra-genetics/commit/76c3ed89dea6629a4f5b491d613cd66d2c91e28e))

## [3.1.0](https://github.com/hydra-genetics/hydra-genetics/compare/v3.0.0...v3.1.0) (2024-10-30)


### Features

* hotspot report can handle missing VEP annotaiton ([174d7b0](https://github.com/hydra-genetics/hydra-genetics/commit/174d7b04cd0951388552b570528a2f39cfb48bfb))


### Bug Fixes

* change to append to handle string output properly ([bef4d6c](https://github.com/hydra-genetics/hydra-genetics/commit/bef4d6c362ee72f6027c07f43212d1f1aa951012))
* crash if pipeline dir is not a git repo ([#373](https://github.com/hydra-genetics/hydra-genetics/issues/373)) ([de667e0](https://github.com/hydra-genetics/hydra-genetics/commit/de667e03c5b68c2d7e49df156452d99c620ccea5))
* handle missing VEP annotation ([a5a929d](https://github.com/hydra-genetics/hydra-genetics/commit/a5a929df815555b7308c6829ae00889fc7491bbb))
* Handling of missing multiqc module ([6b0d4b6](https://github.com/hydra-genetics/hydra-genetics/commit/6b0d4b62aa59addc82d041fe0b838bd2ce7f096a))
* update python action ([266f849](https://github.com/hydra-genetics/hydra-genetics/commit/266f849bf0337360e5b396ab1c6edcfab7d15ad8))

## [3.0.0](https://github.com/hydra-genetics/hydra-genetics/compare/v2.0.1...v3.0.0) (2024-05-30)


### ⚠ BREAKING CHANGES

* output software versions into one file  ([#361](https://github.com/hydra-genetics/hydra-genetics/issues/361))

### Features

* output software versions into one file  ([#361](https://github.com/hydra-genetics/hydra-genetics/issues/361)) ([155f557](https://github.com/hydra-genetics/hydra-genetics/commit/155f55740d8ef8ab3f1b044247692443754922c0))
* report all region_all variants in cov_and_mut ([98dc4f6](https://github.com/hydra-genetics/hydra-genetics/commit/98dc4f6e1f747ab39f7d05e9083a2d2026816010))


### Bug Fixes

* filter more one docker labels ([19a23cf](https://github.com/hydra-genetics/hydra-genetics/commit/19a23cf5dd91dff351823ff37f19f964eec153cd))
* handle remote on local file the same ([2e02578](https://github.com/hydra-genetics/hydra-genetics/commit/2e025780b83c49d849e338ef6444804a6110c2d5))

## [2.0.1](https://github.com/hydra-genetics/hydra-genetics/compare/v2.0.0...v2.0.1) (2024-04-25)


### Bug Fixes

* name and version extraction from name_and_version split ([b2267ac](https://github.com/hydra-genetics/hydra-genetics/commit/b2267ac05ab8037ae8e23c4ba5f51d8838091eee))

## [2.0.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.14.0...v2.0.0) (2024-04-24)


### ⚠ BREAKING CHANGES

* make platform required for create-input-files

### Features

* create input files from long read bam files ([b75e37f](https://www.github.com/hydra-genetics/hydra-genetics/commit/b75e37f9693033844fa3c48c326fb2e95d218cf2))
* create input files from long read bam files ([5a96e9f](https://www.github.com/hydra-genetics/hydra-genetics/commit/5a96e9fa36f21990cf8e951a50019e444eb4b786))
* make platform required for create-input-files ([0f86f41](https://www.github.com/hydra-genetics/hydra-genetics/commit/0f86f413a425220bf1508b6b1ec8a39406854348))
* update handling of version extraction and added test ([45212b5](https://www.github.com/hydra-genetics/hydra-genetics/commit/45212b57f6b3441da0bedc9b49727b644ab05e76))
* Update units.schema.yaml for long read ([aec2708](https://www.github.com/hydra-genetics/hydra-genetics/commit/aec2708607c8f6814337ef293ea548c2d8f1920f))


### Bug Fixes

* fix typo in warning message ([d1a77d2](https://www.github.com/hydra-genetics/hydra-genetics/commit/d1a77d2775adf4ebe969c2807958cc3b539898ae))
* minor updates to pipeline template ([bff9861](https://www.github.com/hydra-genetics/hydra-genetics/commit/bff9861e0fd2b602aacf078b6d574e2e5c55bc06))
* **utils:** change container re search pattern ([8594a9d](https://www.github.com/hydra-genetics/hydra-genetics/commit/8594a9d8100160aad075902b8db733c2f08f0df8))


### Documentation

* add badge for mkdocs ([259eedc](https://www.github.com/hydra-genetics/hydra-genetics/commit/259eedc9b2dd00d59eb30c935e9f36e8d534d2c9))
* update import from tool versions ([011ea60](https://www.github.com/hydra-genetics/hydra-genetics/commit/011ea60a35a923fac7e18d64f6d667d1094f143e))

## [1.14.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.13.0...v1.14.0) (2024-03-01)


### Features

* add touch functions for version files ([07e190b](https://www.github.com/hydra-genetics/hydra-genetics/commit/07e190bc78aeefc2d99284a872c445c9918ead78))


### Bug Fixes

* change mkdir to makedirs  ([d252b76](https://www.github.com/hydra-genetics/hydra-genetics/commit/d252b7610d0517275b59c46a4a6ddee77b7d17cd))
* minor update to output filename for pipeline version ([a4d3475](https://www.github.com/hydra-genetics/hydra-genetics/commit/a4d347598865e2139d70155eb65c8326c9a014d9))


### Documentation

* add missing variable to example ([5762058](https://www.github.com/hydra-genetics/hydra-genetics/commit/57620587e8701676373f90c63cdec2f555d3476a))
* change filename ([f3a28a1](https://www.github.com/hydra-genetics/hydra-genetics/commit/f3a28a1a89f43dbf9bc5020de2c093b94a855543))

## [1.13.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.12.0...v1.13.0) (2024-02-29)


### Features

* add functions used to annotate config with software versions ([f541a2b](https://www.github.com/hydra-genetics/hydra-genetics/commit/f541a2bca4c630a2ff7a83ffcb3f96ef16d2ea4f))
* add max_version function and update documentation. ([4e532e3](https://www.github.com/hydra-genetics/hydra-genetics/commit/4e532e3424408ad197101c29a051b35fc4d31356))
* function used to print pipeline version ([83b4e96](https://www.github.com/hydra-genetics/hydra-genetics/commit/83b4e96c716dc58b63a695443bb5973a991d0dcc))


### Documentation

* small correction in documentation ([984263f](https://www.github.com/hydra-genetics/hydra-genetics/commit/984263f0b35c48513f5a3537a83fbe261e09938b))

## [1.12.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.11.1...v1.12.0) (2024-02-21)


### Features

* update handling of reference files ([70ba91f](https://www.github.com/hydra-genetics/hydra-genetics/commit/70ba91fd082fc31b7a26bafea21b2331ef8f6e1c))


### Bug Fixes

* handle tumour content set to 0 when creating sample.tsv ([cb96b5d](https://www.github.com/hydra-genetics/hydra-genetics/commit/cb96b5d570bd5cddb531c614b5704edbab9240e4))

### [1.11.1](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.11.0...v1.11.1) (2024-02-02)


### Bug Fixes

* match latest settings format ([1727c12](https://www.github.com/hydra-genetics/hydra-genetics/commit/1727c12475ff1d1ccd63cef92f7bc5a1f2157c9d))

## [1.11.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.10.2...v1.11.0) (2024-01-30)


### Features

* lock pulp version in pipeline template ([7f7fe41](https://www.github.com/hydra-genetics/hydra-genetics/commit/7f7fe41376714f298385b08387903beca096ab08))
* make it possible to populate samples and units with data from json file ([e5ec03b](https://www.github.com/hydra-genetics/hydra-genetics/commit/e5ec03b1f1ddab8fd6708c0106cf6297f423ebbc))
* update snakefmt linter version for pipeline template ([05c39a4](https://www.github.com/hydra-genetics/hydra-genetics/commit/05c39a48afada7a583ba79c22519858884e398f2))


### Performance Improvements

* improve performance and fix minor issue ([a109221](https://www.github.com/hydra-genetics/hydra-genetics/commit/a109221868f5a30f73364e57ad25f9e1d20d5b05))

### [1.10.2](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.10.1...v1.10.2) (2023-12-20)


### Bug Fixes

* return None when empty string in vep annotation ([636a53a](https://www.github.com/hydra-genetics/hydra-genetics/commit/636a53ab35b5fa4b0810f5b8e9caa2acc1fde4ea))

### [1.10.1](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.10.0...v1.10.1) (2023-12-19)


### Bug Fixes

* bug in vep annotation handling ([60dce4e](https://www.github.com/hydra-genetics/hydra-genetics/commit/60dce4e7c8c80ab1fc72af8f413a1a6de7c71f53))
* handle missing transcipt in annotation by using pick ([f72af94](https://www.github.com/hydra-genetics/hydra-genetics/commit/f72af9494d526867a554eded059e056bfef816c7))

## [1.10.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.9.1...v1.10.0) (2023-12-08)


### Features

* added handling and selection between multiple transcripts in hotspot report ([5aeb2c6](https://www.github.com/hydra-genetics/hydra-genetics/commit/5aeb2c693fa3d60b799e6983c50701c606107d55))


### Bug Fixes

* pycodestyle ([2fa0e64](https://www.github.com/hydra-genetics/hydra-genetics/commit/2fa0e64e6b96f4b4693d6e9d6e8da495fe188bd7))
* wrong vcf files used ([d3dbbe1](https://www.github.com/hydra-genetics/hydra-genetics/commit/d3dbbe1568b76a20ef3eb37a1088aa37f4c2606b))

### [1.9.1](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.9.0...v1.9.1) (2023-11-29)


### Bug Fixes

* handle list of str when replacing config variables ([30223f4](https://www.github.com/hydra-genetics/hydra-genetics/commit/30223f404a05517dce0187adb39de4679848a23f))

## [1.9.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.8.1...v1.9.0) (2023-11-13)


### Features

* add test build mkdocs to template ([e08b1ad](https://www.github.com/hydra-genetics/hydra-genetics/commit/e08b1ad377ca78fc0174de0b64b5033f9351f5b6))


### Bug Fixes

* handle case when requested number of reads couldn't be selected ([088f0b1](https://www.github.com/hydra-genetics/hydra-genetics/commit/088f0b130728d728922af6dbb61762046db86475))
* handle events when a file is listed multiple times in the config ([812c8e8](https://www.github.com/hydra-genetics/hydra-genetics/commit/812c8e843265bc5508f69f8b1acea3fb060f128a))


### Documentation

* update  mkdocs plugin yaml and rule versions ([816ddbb](https://www.github.com/hydra-genetics/hydra-genetics/commit/816ddbb7d8e09776718dfcd75ea5de230fd3fd65))
* update hydra-genetics version in docs and templates ([8a91779](https://www.github.com/hydra-genetics/hydra-genetics/commit/8a9177938a44038cfbb70cbf3468e56eb01d0af1))

### [1.8.1](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.8.0...v1.8.1) (2023-09-07)


### Bug Fixes

* handle missing parent directories ([d7d47d6](https://www.github.com/hydra-genetics/hydra-genetics/commit/d7d47d669b5ad2feb767303290f7a8261a243b10))
* remove code ([4b1752b](https://www.github.com/hydra-genetics/hydra-genetics/commit/4b1752b384b023cdfdd4fd352d24b12d152a5906))

## [1.8.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.7.0...v1.8.0) (2023-09-06)


### Features

* make it possible to define links when fetching data ([35fa20a](https://www.github.com/hydra-genetics/hydra-genetics/commit/35fa20aec38c441d0b7eba0d1d91103b43ac3544))


### Bug Fixes

* reduce memory usage when downloading files ([3e6b4b6](https://www.github.com/hydra-genetics/hydra-genetics/commit/3e6b4b696248d8e5058b7f3ae70f18c780cf6ea5))

## [1.7.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.6.0...v1.7.0) (2023-09-04)


### Features

* function used to add variable optios to a yaml file ([4cc2733](https://www.github.com/hydra-genetics/hydra-genetics/commit/4cc2733c91faaf1a8a7763ed62ed562f1929a67e))
* make it possible to download and decompress zipped files and folders ([2a14a81](https://www.github.com/hydra-genetics/hydra-genetics/commit/2a14a81d2a49aac08c2c4b33a239098fc3a8757e))
* make it possible to split files into smaller parts ([f886244](https://www.github.com/hydra-genetics/hydra-genetics/commit/f88624439e88849c3ec24b173d4ec9615d4e878d))
* make it possible to validate content of compressed files ([cae730c](https://www.github.com/hydra-genetics/hydra-genetics/commit/cae730c1b09eebd587df37fd7c950ef333af383f))
* output more information about download/validation for ref files ([c9524a3](https://www.github.com/hydra-genetics/hydra-genetics/commit/c9524a3daf23a1b132f18d94e1609e6575972dae))


### Bug Fixes

* parent folder bug and remove existing folder if it needs updating ([61032a5](https://www.github.com/hydra-genetics/hydra-genetics/commit/61032a5c7bbdaa4d54e0614e782786d1ffc2354d))


### Documentation

* correcting rtd links ([fcd00c9](https://www.github.com/hydra-genetics/hydra-genetics/commit/fcd00c9e5d9d556e3ff283dcc194b4cb359d4e50))
* update rtd links ([ecb845a](https://www.github.com/hydra-genetics/hydra-genetics/commit/ecb845aa6185a8cfb7a2f782e276e0441e7889d0))
* update rtd links ([153bfe4](https://www.github.com/hydra-genetics/hydra-genetics/commit/153bfe402e75d32b60e3070e710a721a642881e7))

## [1.6.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.5.1...v1.6.0) (2023-06-28)


### Features

* make it possible to entries without url when fetching data ([c41c0e8](https://www.github.com/hydra-genetics/hydra-genetics/commit/c41c0e85bcef868e46595042d8d4f80a3eaf7ec5))


### Bug Fixes

* handle location determination of repositories better for local module ([517bbf5](https://www.github.com/hydra-genetics/hydra-genetics/commit/517bbf59e117916d866608e29b843af5ca5fde78))
* remove conda from template ([93a909f](https://www.github.com/hydra-genetics/hydra-genetics/commit/93a909f5f8787110e0ff974f6d121f3ef7ac2c59))
* set valid common container version in config.yaml ([b59cecc](https://www.github.com/hydra-genetics/hydra-genetics/commit/b59cecc38b6614dfd5983ace8f679f7a1f3b4504))

### [1.5.1](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.5.0...v1.5.1) (2023-06-02)


### Bug Fixes

* minor bug fixes ([437cb97](https://www.github.com/hydra-genetics/hydra-genetics/commit/437cb9754d801ea87cf3c7611730a061ce6be1ba))

## [1.5.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.4.0...v1.5.0) (2023-05-30)


### Features

* cli to fetch/validate reference data ([e3ffeef](https://www.github.com/hydra-genetics/hydra-genetics/commit/e3ffeef6ae54dbf203d7cdd2fdb6ca71570312ea))


### Bug Fixes

* add sys.exit if no --configfile ([d17942f](https://www.github.com/hydra-genetics/hydra-genetics/commit/d17942fa036c34ad24c62745ea28afb24dde80ad))
* create parent folder for references ([54f240d](https://www.github.com/hydra-genetics/hydra-genetics/commit/54f240d922ca0017b593b01d10010aa3801154a5))
* don't look at pipeline files ([95dac27](https://www.github.com/hydra-genetics/hydra-genetics/commit/95dac27fce6a568182eb3290e53066b7ade0e678))
* handle case when array or number is passed to is_file ([86a9f83](https://www.github.com/hydra-genetics/hydra-genetics/commit/86a9f8358c86463d17394544ec5d57e02a0293fb))
* improve validation ([db01db0](https://www.github.com/hydra-genetics/hydra-genetics/commit/db01db0694feb1e9b734d5186b45c73e2331f731))
* incorrect path to `mkdocs.yaml` ([9dcb14f](https://www.github.com/hydra-genetics/hydra-genetics/commit/9dcb14fd0bb1cdea7db50766a2d06974cb0d8de2))
* make style check happy with regex in template for common.smk ([d8473d5](https://www.github.com/hydra-genetics/hydra-genetics/commit/d8473d56ed358a8f3b42b92e7cb12e9e0186b371))
* revert incorrect path to `mkdocs.yaml` ([e35a3ce](https://www.github.com/hydra-genetics/hydra-genetics/commit/e35a3ce3977adc4a75fca027e8df8f32b940c5bb))
* update dry-run workflow to match latest template ([ff835ac](https://www.github.com/hydra-genetics/hydra-genetics/commit/ff835acacf7ee8a809d8516b636fd9e337985a87))
* update lint workflow to match current template ([82b8370](https://www.github.com/hydra-genetics/hydra-genetics/commit/82b83706b310eaaa3df202194c46b1e0e7b02dfa))
* update readthedocs with correct mkdocs,yaml file name ([89e52d3](https://www.github.com/hydra-genetics/hydra-genetics/commit/89e52d3df4142b90d18999dec45aedc4378dcda2))
* update snakefmt workflow to match latest template ([b9ef634](https://www.github.com/hydra-genetics/hydra-genetics/commit/b9ef634cf0e9a1bad002233a3d001da0e9e28901))
* update test links in template ([a49afff](https://www.github.com/hydra-genetics/hydra-genetics/commit/a49afff172874ef691f39a23037083f78ae31591))


### Documentation

* spelling ([34e9ce2](https://www.github.com/hydra-genetics/hydra-genetics/commit/34e9ce2d61a52f8185236d8a4203cf74969ebf61))

## [1.4.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.3.0...v1.4.0) (2023-05-16)


### Features

* add output yaml file to pipeline template integration test ([231bede](https://www.github.com/hydra-genetics/hydra-genetics/commit/231bededd41faee8a6ef008ca2303f77199dfe9f))
* for pipeline template, change branch name master to main ([fff35d8](https://www.github.com/hydra-genetics/hydra-genetics/commit/fff35d85e0700628d687d80c789fcc4fea9f6d51))
* make read regex less stringent ([44439b6](https://www.github.com/hydra-genetics/hydra-genetics/commit/44439b61c32d1d25e3940bf4ec71583a67c7d596))
* remove dropna for units ([2146cfa](https://www.github.com/hydra-genetics/hydra-genetics/commit/2146cfafe9d4faf7a11539aa88de0d33c8d022af))
* update pipeline template, change to yaml as deault for output_files ([5065898](https://www.github.com/hydra-genetics/hydra-genetics/commit/5065898cb74a6eac31b01216cfabf7f6babc55cd))
* update snakemake versionm allow range up to version 8 ([e0d9b19](https://www.github.com/hydra-genetics/hydra-genetics/commit/e0d9b192a5b22352670a72e2e7307037bb9b8cff))


### Bug Fixes

* add preserve timestamp to output rule function ([0e3e779](https://www.github.com/hydra-genetics/hydra-genetics/commit/0e3e779fd58d68c1fc7b5c22020f8635a7efd4a7))
* cli spelling error ([06011dc](https://www.github.com/hydra-genetics/hydra-genetics/commit/06011dce1e57ccde22b25498d76105ba353ea68f))
* sort entries in template resources.schema.yaml in alphabetically order ([9eb85ac](https://www.github.com/hydra-genetics/hydra-genetics/commit/9eb85ac57dd8e69f88716eced51d97869d8abb78))


### Documentation

* Update skeleton_rule.smk message ([63109e7](https://www.github.com/hydra-genetics/hydra-genetics/commit/63109e7f3336d83d32d4bcf4c3bbe94618f459df))

## [1.3.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.2.0...v1.3.0) (2023-05-10)


### Features

* update hydra-genetics version for template ([808687a](https://www.github.com/hydra-genetics/hydra-genetics/commit/808687a7db4a61594a85b9433738ae36d1bac7a7))


### Bug Fixes

* add missing library name and update variable name ([7e5d32d](https://www.github.com/hydra-genetics/hydra-genetics/commit/7e5d32dfebcf7b50b7c0b025dd9bd2d3f66ec7f9))
* update output list function ([7aee418](https://www.github.com/hydra-genetics/hydra-genetics/commit/7aee4182dcdae4ce107a719abf7d14b26e8386fd))


### Documentation

* add command to download reference and fastq data from gdrive ([bf4f788](https://www.github.com/hydra-genetics/hydra-genetics/commit/bf4f788992607a81338489a15a7ffd6cab438e0e))
* add missing \ to tutorial command ([1d38a0e](https://www.github.com/hydra-genetics/hydra-genetics/commit/1d38a0eadd816bee407350622d94ab2f5e7460cb))
* bump hydra-genetics version ([eeefbfc](https://www.github.com/hydra-genetics/hydra-genetics/commit/eeefbfc1d2ac0ea2ed76066856b1e1c78169dc0d))
* bump hydra-genetics version ([2046064](https://www.github.com/hydra-genetics/hydra-genetics/commit/2046064c7c059a37554c41c6246c38d2d67aa014))
* download test data later ([b664f5a](https://www.github.com/hydra-genetics/hydra-genetics/commit/b664f5a38a803aa0f1dd94cdd4c79f7b814b2525))
* update tutorial ([46c63e7](https://www.github.com/hydra-genetics/hydra-genetics/commit/46c63e75aafcba13c52cc0cd6e541dd3d39c71c5))
* update tutorial ([ec375ef](https://www.github.com/hydra-genetics/hydra-genetics/commit/ec375ef96a955d002e95dd7c19cdfd7a5c6df991))

## [1.2.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.1.0...v1.2.0) (2023-05-09)


### Features

* output list/rule copy function added. ([57d9840](https://www.github.com/hydra-genetics/hydra-genetics/commit/57d98407f4603eb0ec1ec38e84165ddb97e766ae))
* remove dummy rule ([2d5a3d8](https://www.github.com/hydra-genetics/hydra-genetics/commit/2d5a3d881ff8bd3feb9cce26e2051030df7d58f9))
* remove report since it not used ([f9c8af0](https://www.github.com/hydra-genetics/hydra-genetics/commit/f9c8af0803c5718098177b5228fa90b792356489))


### Bug Fixes

* add abs path template for png copying ([553f622](https://www.github.com/hydra-genetics/hydra-genetics/commit/553f622e86b1aa84b75dfff8e5ed06c6082273bb))
* add barcode to units schema ([a3f980a](https://www.github.com/hydra-genetics/hydra-genetics/commit/a3f980a81b730095938c014b853b5b54b0cb21d6))
* change to correct parameter name ([d55270b](https://www.github.com/hydra-genetics/hydra-genetics/commit/d55270b86883013534b756c7277e32deefc45d05))


### Documentation

* added documentation templates ([fa97363](https://www.github.com/hydra-genetics/hydra-genetics/commit/fa9736358b4496d959b5a4ae5db90d5f47a5b554))
* added mkdocs instructions ([f3b5468](https://www.github.com/hydra-genetics/hydra-genetics/commit/f3b54682fa6daa6788d6096de6c45e601517e600))
* updated tutorial ([6c2eb91](https://www.github.com/hydra-genetics/hydra-genetics/commit/6c2eb91f3ab9647eab42d2648d6863f6a1911b2b))

## [1.1.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v1.0.0...v1.1.0) (2023-05-05)


### Features

* update click dep to match snakefmt versions ([e272547](https://www.github.com/hydra-genetics/hydra-genetics/commit

#### CLI
* cli to fetch containers and update config ([a558a18](https://www.github.com/hydra-genetics/hydra-genetics/commit/a558a18fa0732506d103d7ba9e59903a6dfaa20a))
* update cli function used to create new rules ([0be3a24](https://www.github.com/hydra-genetics/hydra-genetics/commit/0be3a2424d37c2a51a692ce5942d9ef13a5e1fb4))


#### Templates
* add mkdocs setup ([9b46bed](https://www.github.com/hydra-genetics/hydra-genetics/commit/9b46bed0c5cf1a1a259f45f0b4937367f5211e4b))
* drop conda support and testing ([387b50d](https://www.github.com/hydra-genetics/hydra-genetics/commit/387b50d5aaf5f2a0d8d4b918053d64053dbed0bb))
/e27254758210a13686d89f77ee71684a47f1b318))
* update project/module template ([1a235ba](https://www.github.com/hydra-genetics/hydra-genetics/commit/1a235ba7889bba5312e8a1fbc3e7537324a3d133))


### Bug Fixes

* config template ([2a93542](https://www.github.com/hydra-genetics/hydra-genetics/commit/2a93542a82653c23ab953134d1b482e9df29ce16))
* replace iteritems() with items() ([508db62](https://www.github.com/hydra-genetics/hydra-genetics/commit/508db621127c0c0195785868508228bf8be51ec8))
* update requirements for pipeline template ([49a127b](https://www.github.com/hydra-genetics/hydra-genetics/commit/49a127bc9e5c941a42f5499b8beb86291c72fa0b))


### Documentation

* remove martin as code owner ([fd61559](https://www.github.com/hydra-genetics/hydra-genetics/commit/fd61559441776b237a40114f2b61b01277670f8f))

## [1.0.0](https://www.github.com/hydra-genetics/hydra-genetics/compare/v0.15.0...v1.0.0) (2023-02-20)


### ⚠ BREAKING CHANGES

* force user to set index from which format field data will be extracted

### Features

* force user to set index from which format field data will be extracted ([dc9bafd](https://www.github.com/hydra-genetics/hydra-genetics/commit/dc9bafd236abd5c67e6eeb934b5547d500a9adf3))
* rename pycodestyle template gitaction file ([105c6bc](https://www.github.com/hydra-genetics/hydra-genetics/commit/105c6bc93c4e39168a5b1177544cf05018f98abf))
* rename template integration file ([064e8b6](https://www.github.com/hydra-genetics/hydra-genetics/commit/064e8b61eea704349963874437371595d55896bc))
* update project template ([0988d0e](https://www.github.com/hydra-genetics/hydra-genetics/commit/0988d0ee28a42afbed6b8adf8539b221d0ab4513))


### Documentation

* updated name to correspond to the module name change ([18791fe](https://www.github.com/hydra-genetics/hydra-genetics/commit/18791fea96ed3657416e3c01f7e408c7fc9579c2))

## [0.15.0](https://www.github.com/hydra-genetics/tools/compare/v0.14.1...v0.15.0) (2022-09-06)


### Features

* **comman:** update workflow name regex ([3261aaf](https://www.github.com/hydra-genetics/tools/commit/3261aafff9b4710c8d692e00ec62051e940cd114))
* function used to switch between github and local repos ([520bbf3](https://www.github.com/hydra-genetics/tools/commit/520bbf380e3ef9133900aad41448ce08d6e5f704))


### Bug Fixes

* update warning raised when tools tries to calculate barcode sequence  and fails to select preferred number of reads ([6423239](https://www.github.com/hydra-genetics/tools/commit/642323943f42096e7a36a09eb9dcd75b5e12f9ef))

### [0.14.1](https://www.github.com/hydra-genetics/tools/compare/v0.14.0...v0.14.1) (2022-08-26)


### Bug Fixes

* **utils:** update handling for retrieval of data using function ([ab4ca3f](https://www.github.com/hydra-genetics/tools/commit/ab4ca3f53097489fcb24b1fdd93f92c81b7115eb))

## [0.14.0](https://www.github.com/hydra-genetics/tools/compare/v0.13.2...v0.14.0) (2022-08-25)


### Features

* make it possible to select one ore more of specified data sources ([577764a](https://www.github.com/hydra-genetics/tools/commit/577764a50a6c53f65ce330526563fc7c584c2a2d))


### Bug Fixes

* skeleton rule to pass snakefmt ([380233f](https://www.github.com/hydra-genetics/tools/commit/380233f44f524bbe32e7827061bae8823c70ce66))

### [0.13.2](https://www.github.com/hydra-genetics/tools/compare/v0.13.1...v0.13.2) (2022-07-06)


### Bug Fixes

* format log messages ([26bfb4a](https://www.github.com/hydra-genetics/tools/commit/26bfb4a4eb8bdc33760f9acee7ec36201b79c722))

### [0.13.1](https://www.github.com/hydra-genetics/tools/compare/v0.13.0...v0.13.1) (2022-07-05)


### Bug Fixes

* update handling of formatting of report values ([23c9b37](https://www.github.com/hydra-genetics/tools/commit/23c9b375106cbb930239d86894c497df91659efc))

## [0.13.0](https://www.github.com/hydra-genetics/tools/compare/v0.12.0...v0.13.0) (2022-07-03)


### Features

* update module/pipeline template ([26537c4](https://www.github.com/hydra-genetics/tools/commit/26537c4858523a6e7555c3c98138736c78a2297d))


### Bug Fixes

* handle hotspot formatting errors better ([8c712b0](https://www.github.com/hydra-genetics/tools/commit/8c712b0ca6cbeb6827ad9906d62546e0d47ae88d))

## [0.12.0](https://www.github.com/hydra-genetics/tools/compare/v0.11.0...v0.12.0) (2022-06-17)


### Features

* fix template for github actions ([01ba5e0](https://www.github.com/hydra-genetics/tools/commit/01ba5e093537e3a44a699aabe014930ecb4e2243))
* make config.yaml location more flexible ([c8eaef1](https://www.github.com/hydra-genetics/tools/commit/c8eaef18b06ae1c47bf5b66649d55dbe17e2b9a1))
* make configfile/configfiles argument mandatory ([88f5fe9](https://www.github.com/hydra-genetics/tools/commit/88f5fe923fd02d9e93d6d24b0d1dd6136f67c3fa))
* make it possible to format string and values ([ac4624e](https://www.github.com/hydra-genetics/tools/commit/ac4624eb31286a430fac1bc6c183ad63527035b0))


### Bug Fixes

* handle bug the arise when specifying output folder ([9ea716f](https://www.github.com/hydra-genetics/tools/commit/9ea716f72ec264ff6ebc53c8bcd64103c2440f9c))
* make it possible to set a default barcode ([1f0008f](https://www.github.com/hydra-genetics/tools/commit/1f0008f51331c915d107ea62d1de57fff760f979))

## [0.11.0](https://www.github.com/hydra-genetics/tools/compare/v0.10.1...v0.11.0) (2022-05-17)


### Features

* extrac_chr return list with empty string if file not exist ([dcf1afb](https://www.github.com/hydra-genetics/tools/commit/dcf1afb2f7602c35a5c66359fcf7250e341d85b0))

### [0.10.1](https://www.github.com/hydra-genetics/tools/compare/v0.10.0...v0.10.1) (2022-05-16)


### Bug Fixes

* make it possible to add more rules(commands) to a existing smk file. ([d8aec9a](https://www.github.com/hydra-genetics/tools/commit/d8aec9a41ed77badbfefc5f1f989a856ab9f54ba))
* update hydra-genetics version in template ([5f1b6cb](https://www.github.com/hydra-genetics/tools/commit/5f1b6cb5b1a1e961a00d39b5c7d71a6e4a6398a3))


### Documentation

* update readme with more examples ([fb6d2ee](https://www.github.com/hydra-genetics/tools/commit/fb6d2eebe0067740299b1155416047ad86c1a103))

## [0.10.0](https://www.github.com/hydra-genetics/tools/compare/v0.9.2...v0.10.0) (2022-04-22)


### Features

* add function used to set min version for hydra-genetics ([a45b8a0](https://www.github.com/hydra-genetics/tools/commit/a45b8a0c57cda85a9fd63059907ac518a710daa8))


### Bug Fixes

* add barcode as index ([970c6a8](https://www.github.com/hydra-genetics/tools/commit/970c6a83bc3bf4ffe3b7a74d8e7a52920f357834))
* exit of no files are found ([83ee81d](https://www.github.com/hydra-genetics/tools/commit/83ee81d5bf0b314e667d1d09559779cd4830d6a8))

### [0.9.2](https://www.github.com/hydra-genetics/tools/compare/v0.9.1...v0.9.2) (2022-03-29)


### Bug Fixes

* added barcode to get_unit filter ([903cb8e](https://www.github.com/hydra-genetics/tools/commit/903cb8eacae5bda19853dcf305f851f21816e600))
* update to comply with latest guidelines ([dc15b5b](https://www.github.com/hydra-genetics/tools/commit/dc15b5b8713af275995d24ef8f88f459087fb908))

### [0.9.1](https://www.github.com/hydra-genetics/tools/compare/v0.9.0...v0.9.1) (2022-03-10)


### Bug Fixes

* add gcvf_depth_field to other variants and found hotspot variants ([ba2a39e](https://www.github.com/hydra-genetics/tools/commit/ba2a39e35ebfd07cde5f8a171d4a451eddb3e50c))

## [0.9.0](https://www.github.com/hydra-genetics/tools/compare/v0.8.0...v0.9.0) (2022-03-10)


### Features

* make it possible to change depth field ([32b385c](https://www.github.com/hydra-genetics/tools/commit/32b385c10b13aed1dda3f5d242014f42c1a3c903))

## [0.8.0](https://www.github.com/hydra-genetics/tools/compare/v0.7.0...v0.8.0) (2022-03-09)


### Features

* make it possible to combine columns in hotspot report. ([5d21af8](https://www.github.com/hydra-genetics/tools/commit/5d21af830f301f89f178660f9f1e1a0470e39d37))


### Bug Fixes

* change TC to tumor_content ([31d8d6b](https://www.github.com/hydra-genetics/tools/commit/31d8d6b1e2b8f2741e5212c9b5dc41db2df07073))

## [0.7.0](https://www.github.com/hydra-genetics/tools/compare/v0.6.0...v0.7.0) (2022-03-07)


### Features

* clean test requirements ([10f3f67](https://www.github.com/hydra-genetics/tools/commit/10f3f67fed81693ad39f8e10ddd36b26cf62f9ae))

## [0.6.0](https://www.github.com/hydra-genetics/tools/compare/v0.5.0...v0.6.0) (2022-03-03)


### Features

* return None with missing/empty annotation data ([aa19bc8](https://www.github.com/hydra-genetics/tools/commit/aa19bc8537612731b9aadabe2358f1c7497635de))


### Bug Fixes

* change name of testrun-commands workflow ([86f49d7](https://www.github.com/hydra-genetics/tools/commit/86f49d7519ac9c6c61705b441b2b2f5170ba123b))
* correct syntax error and handle return None value ([3d93271](https://www.github.com/hydra-genetics/tools/commit/3d9327144672a705664b0918503c30a7987f31ed))
* set correct indentation for config.schema.yaml ([5f43478](https://www.github.com/hydra-genetics/tools/commit/5f4347875f6cc4cedbf2e923797ac6df94911c62))
* set correct indentation for resources.schema.yaml ([048dcad](https://www.github.com/hydra-genetics/tools/commit/048dcadd82bb390ad36e6ee2cb3e8bae5c541bb8))

## [0.5.0](https://www.github.com/hydra-genetics/tools/compare/v0.4.0...v0.5.0) (2022-02-22)


### Features

* make it possible to output found sample and read part. ([09c3448](https://www.github.com/hydra-genetics/tools/commit/09c34486d904ccff6cee8d60a8161b7dcaba9a0e))
* test that commands can be run using workflow. ([103f534](https://www.github.com/hydra-genetics/tools/commit/103f5346284652cdf36931781307ce48f9883435))


### Bug Fixes

* escape curly brackets in conventional-prs workflow. ([8114d14](https://www.github.com/hydra-genetics/tools/commit/8114d148eb7523c3ac407f57d43fe863777e9c8f))
* update barcode extraction from read name to handle trailing slash followed by 1 or 2 ([118a8ef](https://www.github.com/hydra-genetics/tools/commit/118a8ef19d26924b1b02167a8e6bf0b2b6f95589))
* use correct dict variable name ([70ba2d1](https://www.github.com/hydra-genetics/tools/commit/70ba2d1df4e93279fe0fb754bb54db7908225fa4))

## [0.4.0](https://www.github.com/hydra-genetics/tools/compare/v0.3.0...v0.4.0) (2022-02-18)


### Features

* add workflow for semantic check to template ([58dfec1](https://www.github.com/hydra-genetics/tools/commit/58dfec1651b37ed81753703990692ee5eddef4c3))
* update hydra-genetics requirements in template to 0.3.0 ([ca5f0a6](https://www.github.com/hydra-genetics/tools/commit/ca5f0a6ed0c37fc58fdc6f99cdc147ee504f9618))


### Bug Fixes

* correct failing pip install due to build env ([8b13081](https://www.github.com/hydra-genetics/tools/commit/8b130817f924834051785ebd214592f2ce520d9c))

## [0.3.0](https://www.github.com/hydra-genetics/tools/compare/v0.2.9...v0.3.0) (2022-02-09)


### Features

* semantic control of commits and please-realse workflow ([9e34116](https://www.github.com/hydra-genetics/tools/commit/9e34116e22a3be042a7a30cffe23a227d210aeca))


### Bug Fixes

* change-package name and set default-branch. ([10d2756](https://www.github.com/hydra-genetics/tools/commit/10d2756a642caaa3e62f7dd9f03adb16eef44dcd))
* correct syntax for conventional-prs workflow ([cd307ff](https://www.github.com/hydra-genetics/tools/commit/cd307ff9a8a89d9e3807d929a2a6dcc47042892d))
* fix invalid syntax in releas-please workflow ([7ac3a45](https://www.github.com/hydra-genetics/tools/commit/7ac3a457af94439d31dc7f8c7e7731e172c05d30))
