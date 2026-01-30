## Release History

### 2.1.14
- Bugfix for certain paginated endpoints

### 2.1.13
- Support for paginated code run and code object endpoints

### 2.1.12
- Refactored project collaboration methods.

### 2.1.11
- Added support for patch method to rest handler and session class
- Added support for rename method to code object class

### 2.1.10.
- Change the error message when fetching a model's weights 
- Refactored RhinoSDKException

### 2.1.9
- Support for Intra Project Privacy

### 2.1.8
- Fix issue with dataset endpoints

### 2.1.7
- Updated ECR repository URL for new repo setup.

### 2.1.6.
- Fix for get_container_image_uri. 
- Added support for vocabulary terms pagination

### 2.1.5.
- Add support for Iris-Intersystem DB for sql query. 

### 2.1.4.
- Bugfix

### 2.1.3.
- Remove the report_images field from the CodeRun dataclass, as it is no longer provided by the API.

### 2.1.2.
- Bugfix

### 2.1.1.
- Add support for running SDK behind institutional firewalls

### 2.1.0.
- Add Data Harmonization endpoints
- Internal refactor

### 2.0.1.
- Fix default arguments in CodeObjectCreatInput.

### 2.0.0.
- Add initial support for python 3.13
- REMOVED SUPPORT FOR PYTHON 3.8
- Fixed endpoints for removing objects
- Added endpoint to get file transfer information
- Add support for session resumption
- Cleanup internal code

### 1.5.2.
- Add support for NVFlare v2.6.

### 1.5.1.
- Add support for model catalogs - publishing and unpublishing Code Objects and Code Runs.

### 1.5.0.
- Add enhanced support for processing sensitive data. Required upgrade to continue working with FCP (though all changes are backwards compatible, so no code changes needed).

### 1.4.3.
- Replace semantic mapping vocabulary filters with simpler vocabulary categories. 

### 1.4.2.
- Add support for setting Homomorphic Encryption parameters for NVFlare model training.

### 1.4.1.
- Improved internal API communication. 

### 1.4.0.
- Add support for the new Rhino Health API.

### 1.3.11.
- Rename get_container_uri to get_container_image_uri.

### 1.3.10.
- Handle workgroups with no image repo and/or storage bucket.

### 1.3.9.
- Add a session.get_container_uri helper method, add additional Workgroup attributes.

### 1.3.8.
- Add a RhinoCloud object to encapsulate interactions with the Rhino Cloud API.

### 1.3.7.
- Add support for storage multiple zip code locations in auto-containers code object.

### 1.3.6
- Standardize new Rhino Health environment URLs

### 1.3.5
- Add support for uploading files to GCS in auto-containers code object.

### 1.3.4
- Add support for NVFlare v2.5.

### 1.3.3
- Add support for optional and/or list input datasets in code objects and code runs

### 1.3.2
- Make transformation definition optional (by default will use source data)

### 1.3.1
- New Custom Mapping support for Data Harmonization

### 1.3.0
- Add support for Data Harmonization

### 1.2.1
- Fixed missing output_dataset_uids in synchronous code run responses.

### 1.2.0
- Support for the FCP backend no longer creating code run output datasets in advance.

### 1.1.2
- Fixes to run code dataclasses. CodeFormat is now renamed CodeLocation (old enum is deprecated)

### 1.1.1
- Fixed an issue where code_run.results_report was not allowed to be populated by dicts.  

### 1.0.10
- Add support for NVFlare v2.4.

### 1.0.9
- Added support for the Wilcoxon signed rank test.

### 1.0.8
- Added indication of request's origin being the SDK.

### 1.0.7
- Added support for Spearman's Rank Correlation Coefficient.

### 1.0.6
- Added support for the Pearson Correlation Coefficient.
- Added support for the Intraclass Correlation Coefficient.

### 1.0.5
- Converted data schema to be only single project.

### 1.0.4
- Added support for run time external files.

### 1.0.3
- Added support for the Cox Proportional Hazards model metric.

### 1.0.2
- Add improved support for uid fields with addition of naming
- Improved documentation

### 1.0.0
This is a major version that features breaking changes. It is a required upgrade, since it reflects changes made in the Rhino FCP API.

to the Rhino Health SDK. Please read the changelog and communications carefully.
https://docs.rhinohealth.com/hc/en-us/articles/16016581053341
- Pydantic is now upgraded to version 2 for improved security
- Now using upgraded version of typing extensions and requests
- Cohorts are now called Datasets
- AIModels are now called CodeObjects
- ModelResult are now called CodeRuns
- Dataschema is now DataSchema in the code to be consistent with two word naming pattern
- Removed old deprecated functions and inputs
> - `CodeObject.version` was never used and removed
> -  `CodeObject.input_dataschema_uid` and `CodeObject.output_data_schema_uid` are removed, please use `input_data_schema_uids` and `output_data_schema_uids`
> -  `DataSchema.projects_uid` is removed
> -  Historical references to `dataschema`, please use `data_schema` instead
> - There is no longer a distinction between single data schema CodeObject vs Multi data schemas. All creation objects are multi now.
> - `Dataset.run_code` now returns a CodeRun object instead of a RunResponse object.
> - `ModelInferenceAsyncResponse` moved to `code_run_dataclass` from `code_object_dataclass`
> - Fixed bug with schemavariables
> - `Project.status` is now `Project.stats`
> - `model_params_external_storage_path` is now `paths_to_model_params` and fixed issue with reading from wrong location
> - `DataSchema.num_datasets` is no longer available
### 0.3.5
- Added support for getting the currently logged in user

### 0.3.4
- Added the one way ANOVA test metric

### 0.3.3
- Added ability to perform Federated Join Metrics

### 0.3.2
- Added the t-test and chi-squared test metrics

### 0.3.1
- Internal code structure changes

### 0.3.0
- Modified Standard Deviation metric output key to "stddev" (previously "std") 

### 0.2.27
- Add Kaplan Meier metric

### 0.2.26
- Add Epidemiology metrics: TwoByTwoTable, Odds, OddsRatio, Risk, RiskRatio, Prevalence and Incidence.

### 0.2.25
- Add Max and Min metrics

### 0.2.24
- Add ability to build NVFlare containers in a similar manner to instant containers

### 0.2.23
- Add ability to provide multiple files when using instant containers
- Add ability to provide python version and cuda version as a base image when using instant containers
- Add ability to use data schemas when importing a cohort from a sql query 
 
### 0.2.22
> - Fix missing doc-strings for various SDK methods

### 0.2.21
> - Add quantile metrics and cloud-based aggregation

### 0.2.20
> - Several minor fixes and tweaks

### 0.2.19
> - Add ability to get aggregate statistics for standard deviation
> - Reorganized aggregate statistics to allow custom implementations
> - Add ability to download multiple model weights files
> - Add ability to run inference using a previously trained model

### 0.2.18
> - Add ability to query external sql databases
> - Add ability to import cohorts from external sql database queries

### 0.2.17
> - Add ability to halt nvflare model run

### 0.2.16
> - Support for NVFlare 2.3

### 0.2.15
> - Improve supported range of requirements
> - Improve documentation
> - Add support for simulated federated learning

### 0.2.14
> - Add support for build status on AIModel
> - Internal code cleanup
> - Update requirements for the library to reduce chance of errors
> - Add support for Instant Containers on the Rhino Health Platform
> - Fix bug with Dataschema dataclass

### 0.2.13
> - Fix some bugs with run_code
> - Update documentation so users do not use internal only get/post/raw_response methods
> - Add alias for historic use cases of internal only methods with deprecation warnings

### 0.2.12
> - Add support for rate limiting
> - Add ability to query system resources

### 0.2.11
> - Add dataclass for AIModel run and train
> - Update dataclass for modelresult to allow waiting for asynchronous completion
> - cohort.run_code, session.aimodel.run_aimodel, and session.aimodel.train_aimodel 
now all return dataclasses instead of raw responses.
> - Fix bugs with various dataclass properties
> - Fix adding and removing collaborators

### 0.2.10
> - Update support of finding objects by versions

### 0.2.9

> - Completed dataclass for DataSchema to allow creation and pulling of objects
> - dataschema is now renamed to data_schema in the SDK to be consistent,
old usages are still possible but you will receive a deprecation warning. Please use the new way of accessing data_schemas.
> - Experimental endpoint for getting workgroups
> - Fixed some issues with properties on projects
> - Fix issue with get_cohorts()
> - Fixed issue with project.aimodels returning incorrect dataclasses
> - Fixed issue with certain functions not working

### 0.2.8

> - Improved documentation for creating/running AI Models
> - Fixed the bug you reported about training where unset values in the input were being sent to the backend
> - Added ability to search by name as well as a regrouping utility function for the result of metrics
> - Added a new Python Code Generalized Compute Type
