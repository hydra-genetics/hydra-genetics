# Changelog

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
