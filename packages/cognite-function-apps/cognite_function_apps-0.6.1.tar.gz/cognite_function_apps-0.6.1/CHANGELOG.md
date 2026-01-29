# Changelog

## [0.6.1](https://github.com/cognitedata/cognite-function-apps/compare/cognite-function-apps-v0.6.0...cognite-function-apps-v0.6.1) (2026-01-20)


### Bug Fixes

* exclude dependency parameters from MCP schema with PEP 563/649 annotations ([b9c1772](https://github.com/cognitedata/cognite-function-apps/commit/b9c17729753652ac1c49f391455ad9e34e697579))
* exclude dependency parameters with PEP 563/649 annotations ([fb862cb](https://github.com/cognitedata/cognite-function-apps/commit/fb862cb554ea0fea74229235a2b3836d659572eb))
* handle PEP 563/649 string annotations in dependency injection ([a22a190](https://github.com/cognitedata/cognite-function-apps/commit/a22a190f7e33b0e8da54e7cee085e9464213cdde))

## [0.6.0](https://github.com/cognitedata/cognite-function-apps/compare/cognite-function-apps-v0.5.3...cognite-function-apps-v0.6.0) (2025-12-19)

### ⚠ BREAKING CHANGES

* Package renamed from cognite-typed-functions to cognite-function-apps. CLI command renamed from ctf to fun.
* Response customization with status_code and headers ([#141](https://github.com/cognitedata/cognite-function-apps/issues/141))
* Streamlines tracing setup to one line before v1.0. Taking this opportunity to fix the API while adoption is still early.

### Features

* add automatic trace propagation via traceparent header ([f410e2f](https://github.com/cognitedata/cognite-function-apps/commit/f410e2fb75587cfba30c048f083f0dd6a806a87b))
* Add exporter_provider to TracingApp for secret-based authentication ([dabbe4f](https://github.com/cognitedata/cognite-function-apps/commit/dabbe4f22ef595f9e397c0b8a403526e03812f3e))
* make the docs actionable as a tutorial, and smaller. ([6377121](https://github.com/cognitedata/cognite-function-apps/commit/6377121866b6d4dfb92f9748be0fb33477c87e0d))
* More renames ([6586373](https://github.com/cognitedata/cognite-function-apps/commit/6586373b28b4ab567abacd280cd34ebb0ab14bda))
* reduce docs for tracer ([aa27a59](https://github.com/cognitedata/cognite-function-apps/commit/aa27a5962d7fee0bf48f8a96423a24ad999354c6))
* rename SDK to Function Apps ([4c138d3](https://github.com/cognitedata/cognite-function-apps/commit/4c138d3386023e568dce2c0ae1f038e1dacbd832))
* Response customization with status_code and headers ([#141](https://github.com/cognitedata/cognite-function-apps/issues/141)) ([9423f2b](https://github.com/cognitedata/cognite-function-apps/commit/9423f2bc7572b6216bdae6a50108390f425663cf))
* simplify tracing API with backend presets ([7535b3a](https://github.com/cognitedata/cognite-function-apps/commit/7535b3aa9aa0c676770ffc46e0d33e41994ee1fc))
* standardize secret key with actionable error messages ([63a0641](https://github.com/cognitedata/cognite-function-apps/commit/63a0641e015986bfcce0976124598b0097267501))

### Bug Fixes

* configure release-please to use manifest mode ([810fff3](https://github.com/cognitedata/cognite-function-apps/commit/810fff30854e472bffed64603f697bf534366a47))
* remove line_spans from highlight config causing garbled code blocks ([#139](https://github.com/cognitedata/cognite-function-apps/issues/139)) ([4ede4cc](https://github.com/cognitedata/cognite-function-apps/commit/4ede4cc7b84d0f1a05d929739d40e4f712846099))
* update publish workflow to trigger on merge commits ([857f19f](https://github.com/cognitedata/cognite-function-apps/commit/857f19fc2091c2bef1faa13ef45265408bed7f33))
* update release-please workflow to use PAT token ([77cadd2](https://github.com/cognitedata/cognite-function-apps/commit/77cadd2aa97694bd7ed8d04a63af9ac584943e21))
* update version to 0.5.0 and configure release-please annotations ([eeb323b](https://github.com/cognitedata/cognite-function-apps/commit/eeb323bad6354c086b39973283e0d4337f4c0dbb))
* use route content_type in OpenAPI schema responses ([#143](https://github.com/cognitedata/cognite-function-apps/issues/143)) ([dc87c6b](https://github.com/cognitedata/cognite-function-apps/commit/dc87c6b2a391f2fddf29844a8192af7d48269bfa))
* use version-file instead of extra-files for Python version ([72548b9](https://github.com/cognitedata/cognite-function-apps/commit/72548b96ea087b841e621e0d5c5e83daf1190d5a))

### Documentation

* add ADR for response customization ([#138](https://github.com/cognitedata/cognite-function-apps/issues/138)) ([b69180b](https://github.com/cognitedata/cognite-function-apps/commit/b69180ba058cf2a3fa68927967d82c07f58e072b))
* add revert commit type to guidelines ([0389f12](https://github.com/cognitedata/cognite-function-apps/commit/0389f12571aa0288675f0632961a265183ca50ba))
* Auto-generate docs from Python files to get linting and type-checking ([#137](https://github.com/cognitedata/cognite-function-apps/issues/137)) ([6a69fe2](https://github.com/cognitedata/cognite-function-apps/commit/6a69fe2dbed6084ac726b146a9aef7592aecf62d))
* Missing renames ([122c151](https://github.com/cognitedata/cognite-function-apps/commit/122c15123a81cb7a822a397f01bdcf4babcc2070))
* update documentation for response customization (PR 141) ([#144](https://github.com/cognitedata/cognite-function-apps/issues/144)) ([d05763c](https://github.com/cognitedata/cognite-function-apps/commit/d05763cfab94f10928e90e63dec6cdd5e5af7d6b))

### Code Refactoring

* address PR review comments ([30a94e9](https://github.com/cognitedata/cognite-function-apps/commit/30a94e903fa269e16c38849b30d6c77ad9df8d8b))
* consolidate tracing to single exporter path ([8ee34dc](https://github.com/cognitedata/cognite-function-apps/commit/8ee34dcbb73cea2ab692f4f633fcae3e8dcba550))
* use version-file instead of extra-files ([2f49ca5](https://github.com/cognitedata/cognite-function-apps/commit/2f49ca5934758088141102aeebcaa2bd4f781512))

## [0.5.3](https://github.com/cognitedata/cognite-typed-functions/compare/cognite-typed-functions-v0.5.2...cognite-typed-functions-v0.5.3) (2025-11-26)

### Documentation

* add revert commit type to guidelines ([0389f12](https://github.com/cognitedata/cognite-typed-functions/commit/0389f12571aa0288675f0632961a265183ca50ba))

## [0.5.2](https://github.com/cognitedata/cognite-typed-functions/compare/cognite-typed-functions-v0.5.1...cognite-typed-functions-v0.5.2) (2025-11-20)

### Bug Fixes

* update publish workflow to trigger on merge commits ([84c30c7](https://github.com/cognitedata/cognite-typed-functions/commit/84c30c7393e70e9b035732a573317bb0ed1d80f0))

## [0.5.1](https://github.com/cognitedata/cognite-typed-functions/compare/cognite-typed-functions-v0.5.0...cognite-typed-functions-v0.5.1) (2025-11-20)

### Bug Fixes

* update version to 0.5.0 and configure release-please annotations ([3a01001](https://github.com/cognitedata/cognite-typed-functions/commit/3a0100101738d008957075fa73523fb2db5558c6))

## [0.5.0](https://github.com/cognitedata/cognite-typed-functions/compare/cognite-typed-functions-v0.4.0...cognite-typed-functions-v0.5.0) (2025-11-19)

### Features

* add automatic trace propagation via traceparent header ([f410e2f](https://github.com/cognitedata/cognite-typed-functions/commit/f410e2fb75587cfba30c048f083f0dd6a806a87b))

## [0.4.0](https://github.com/cognitedata/cognite-typed-functions/compare/cognite-typed-functions-v0.3.2...cognite-typed-functions-v0.4.0) (2025-11-19)

### ⚠ BREAKING CHANGES

* Streamlines tracing setup to one line before v1.0. Taking this opportunity to fix the API while adoption is still early.

### Features

* Add exporter_provider to TracingApp for secret-based authentication ([dabbe4f](https://github.com/cognitedata/cognite-typed-functions/commit/dabbe4f22ef595f9e397c0b8a403526e03812f3e))
* make the docs actionable as a tutorial, and smaller. ([6377121](https://github.com/cognitedata/cognite-typed-functions/commit/6377121866b6d4dfb92f9748be0fb33477c87e0d))
* reduce docs for tracer ([aa27a59](https://github.com/cognitedata/cognite-typed-functions/commit/aa27a5962d7fee0bf48f8a96423a24ad999354c6))
* simplify tracing API with backend presets ([0ecb671](https://github.com/cognitedata/cognite-typed-functions/commit/0ecb671327e87992ef6baa77b10f8f90fa694a6e))
* standardize secret key with actionable error messages ([63a0641](https://github.com/cognitedata/cognite-typed-functions/commit/63a0641e015986bfcce0976124598b0097267501))

### Bug Fixes

* configure release-please to use manifest mode ([45623b2](https://github.com/cognitedata/cognite-typed-functions/commit/45623b2d39c075c703d8a09d8741120ec21607b5))
* update release-please workflow to use PAT token ([ea6cc26](https://github.com/cognitedata/cognite-typed-functions/commit/ea6cc26bf9c827917a9b974dc44721b4f8995455))
* use version-file instead of extra-files for Python version ([5122824](https://github.com/cognitedata/cognite-typed-functions/commit/51228249b214b74a5cfda5f9e445a000be86f234))

### Code Refactoring

* address PR review comments ([30a94e9](https://github.com/cognitedata/cognite-typed-functions/commit/30a94e903fa269e16c38849b30d6c77ad9df8d8b))
* consolidate tracing to single exporter path ([8ee34dc](https://github.com/cognitedata/cognite-typed-functions/commit/8ee34dcbb73cea2ab692f4f633fcae3e8dcba550))
* use version-file instead of extra-files ([2f49ca5](https://github.com/cognitedata/cognite-typed-functions/commit/2f49ca5934758088141102aeebcaa2bd4f781512))
