# AlazarTech Deployment Tools Change Log

This file contains all important changes to the AlazarTech deployment tools

## [1.6.46] - 2026-01-21
### Fixed
- Azure access identifiers.

## [1.6.45] - 2025-11-27
### Changed
- Specify package name for APM.

## [1.6.44] - 2025-09-29
### Changed
- ATS-SDK name should include arm64 or x86_64 for Linux during registeration to
  website. [#69]

## [1.6.43] - 2025-01-07
### Fixed
- Fix issue where register tool cannot open files when deploying drivers.

## [1.6.41] - 2024-12-12
### Added
- Add ATS9362 to register tool. [#67]

## [1.6.40] - 2024-05-15
### Changed
- Replaced SyncBox with ATSSync.

## [1.6.39] - 2024-04-12
### Added
- Add Syncbox to register tool. [#66]

## [1.6.38] - 2023-11-16
### Added
- Add Windows Firmware Updater to register tool. [#63]

## [1.6.36] - 2023-10-20
### Changed
- Register tool evaluates MD5 content of files locally, instead of 
  getting the value calculated by Azure Storage. [#62]

## [1.6.33] - 2023-10-18
### Changed
- Register tool sets licensed products' (ats-sdk, ats-gpu-xxxx) url
  as download link to latest version of Alazar Package Manager (Windows) 
  or License Key Generator (Linux). [#61]

## [1.6.32] - 2023-10-18
### Changed
- Register tool adds more details to name of licensed products packages.

## [1.6.22] - 2023-09-21
### Fixed
- ATS9637 should have product ID 1031 in register tool. [#60]

## [1.6.21] - 2023-07-19
### Fixed
- Add ATS9637 to register tool. [#59]

## [1.6.20] - 2023-05-09
### Fixed
- Register tool adds REQUIRED to Libats library name. [#57]

## [1.6.19] - 2023-05-02
### Changed
- Register tool sets Libats library in driver category. [#58]
- Register tool adds REQUIRED to Libats library name. [#57]

## [1.6.18] - 2023-03-22
### Fixed
- Register tool able to determine OS looking for "deb". [#56]

## [1.6.17] - 2023-03-09
### Added
- ATSTxxx driver label must be changed to match ATS9xxx driver label. [#55]

## [1.6.16] - 2023-01-17
### Added
- Register Thunderbolt products to website. [#54]

## [1.6.15] - 2022-10-17
### Fixed
- Put product_id in ID field for registration tool. [#53]

## [1.6.14] - 2022-10-11
### Added
- Add ID field to registration tool. [#52]

## [1.6.13] - 2022-09-28
### Fixed
- Package names for linux resources.

## [1.6.12] - 2022-09-27
### Added
- Add French names. [#51]

## [1.6.11] - 2022-09-23
### Added
- Support to register linux resources. [#50]

## [1.6.10] - 2022-09-07
### Added
- Option to send email notification in registration tool. [#49]

### Fixed 
- Driver name field in register tool to have format "ATSXXXX Driver for OS".

## [1.6.9] - 2022-09-07
### Fixed 
- Fix issue introduced in v1.6.8 where name and arch were not passed to payload.

## [1.6.8] - 2022-09-06
### Fixed 
- Add name and arch fields for website registration tool.

### Added
- Add product ID for ATS9376, ATS9380, ATS9428, ATS9437, ATS9442, ATS9453 and
  ATS9473.

## [1.6.7] - 2022-09-02
### Fixed
- Regression introduced in v1.6.6 that caused `register` to fail, raising a
  `KeyError: 'ATS9628'` exception. [#48]

## [1.6.6] - 2022-08-31
### Added
- Add support for driver registration to website. [#47]

## [1.6.5] - 2022-07-17
### Fixed
- Issue that caused windrvsign to stall if the signature failed. [#46]

## [1.6.4] - 2022-06-22
### Fixed
- Fix issue in windrvsign.py that caused the script not to run. [#45]

## [1.6.3] - 2022-06-21
### Added
- Support for windows driver signing. [#43]

## [1.6.2] - 2022-05-26
### Added
- Add exclude field to spec.py to exclude files from pattern. [#42]

## [1.6.1] - 2022-04-28
### Changed
- Prefix production URL in register.py with "www". [#40]
- Make changelogparser emit an error if dates or versions are not in descending
  order. [#41]

## [1.6.0] - 2022-04-25
### Added
- Support for cross-referenced issues. [#38]
- register.py - log target URL. [#39]

## [1.5.4] - 2022-03-16
### Fixed
- Issue where running `createversionfile` on a repo with no existing tag would
  fail. Note that it is necessary for the repo to have a `CHANGELOG.md` file and
  an existing commit for this command to work. [#37]

## [1.5.3] - 2021-12-21
### Added
- Support for Python 3.10. [#36]

## [1.5.2] - 2021-11-03
### Added
- Register uses passfile instead of password. [#34]

## [1.5.1] - 2021-09-14
### Added
- Support for website registration. [#32]

## [1.4.0] - 2021-07-20
### Added
- Support for running createversionfile outside of CI. [#29]

### Changed
- Sign files using alazarsign. [#30]

## [1.3.0] - 2021-03-24
### Added
- createversionfile script. [#28]

## [1.2.2] - 2021-03-23
### Fixed
- Issue that prevented the release of v1.2.1

## [1.2.1] - 2021-03-23
### Fixed
- Issue that prevented the release of v1.2.0

## [1.2.0] - 2021-03-22
### Added
- run-clang-format tool

## [1.1.1] - 2020-11-24
### Fixed
- Remove debugging statements

## [1.1.0] - 2020-11-23
### Added
- Full support for SemVer 2.0.0 version numbers in change logs. [#25]
- Add `-o` option to `changelogparser version`. [#26]

## [1.0.1] - 2020-11-03
### Fixed
- Issue with v1.0.0 release, where deploy failed because of the missing Azure
  python dependency. [#24]

## [1.0.0] - 2020-10-27
### Added
- Support for artifacts upload on Azure blob storage used by
  alazar-package-manager [#23]

## [0.4.2] - 2020-09-02
### Fixed
- Issue with v0.4.1 release, where the package couldn't be installed from PyPI
  [#22]

## [0.4.1] - 2020-05-19
### Changed
- Use new code signing certificate

## [0.4.0] - 2020-05-07
### Added
- Support for ticket references in change log items [#19]

### Fixed
- Issue where H3 tags are not closed properly in changelogparser's HTML output

## [0.3.4] - 2019-10-03
### Fixed
- Issue where deploy did not work correctly with Python 2

## [0.3.3] - 2019-09-27
### Added
- Support for Markdown output
- Support for Python 2.7

## [0.3.2] - 2019-07-23
### Fixed
- Spec file build issue when version log is empty

## [0.3.1] - 2019-07-23
### Fixed
- Build issues when version log is empty

## [0.3.0] - 2019-05-06
### Added
- deploy: split "encrypt" into "compress" and "encrypt". This adds support for
  creating non-password protected ZIP files [#10]
- deploy: add "destdir" option [#11]

### Fixed
- Build issues by using a "version.txt" file for this package

## [0.2.0] - 2019-05-02
### Added
- Support for "YANKED" tag in change log files [#4]
- Add option to publish only encrypted files, and option to read password from
  file. [#6]
- Support publishing to FTP sites [#5]
- Add "tospec" to changelogparser [#8]
- Deploy to AlazarTech's PyPI server [#9]

### Changed
- Make encrypt's default value "no" in deploy.py [#7]

## [0.1.0] - 2019-03-20
### Added
- Change log parser utility [#3]

## [0.0.2] - 2019-01-25
### Fixed
- Make directory copy work even if destination already exists

## [0.0.1] - 2019-01-23
### Added
- Initial version: deploy.py [#1]
