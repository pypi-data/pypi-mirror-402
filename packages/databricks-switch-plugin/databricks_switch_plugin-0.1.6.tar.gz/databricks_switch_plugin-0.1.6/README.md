# Switch
LLM-Powered Code Conversion Plugin for Lakebridge

[![codecov](https://codecov.io/gh/databrickslabs/switch/branch/main/graph/badge.svg?token=YOUR_TOKEN)](https://codecov.io/gh/databrickslabs/switch)

## Project Description
Switch is a Lakebridge transpiler plugin that transforms SQL and other source formats into Databricks-compatible notebooks using Large Language Models (LLMs). As a core component of the Lakebridge migration platform, Switch provides automated code conversion capabilities through a multi-stage processing pipeline designed for large-scale platform migrations.

## Project Support
Please note that all projects in the /databrickslabs github account are provided for your exploration only, and are not formally supported by Databricks with Service Level Agreements (SLAs).  They are provided AS-IS and we do not make any guarantees of any kind.  Please do not submit a support ticket relating to any issues arising from the use of these projects.

Any issues discovered through the use of this project should be filed as GitHub Issues on the Repo.  They will be reviewed as time permits, but there are no formal SLAs for support.

## Using the Project
Switch is primarily designed as a Lakebridge transpiler plugin. To use Switch for code conversion:

1. **Install Lakebridge**: Follow the [Lakebridge documentation](https://databrickslabs.github.io/lakebridge)
2. **Install Switch transpiler**: Use Lakebridge to install the Switch transpiler plugin
3. **Run conversion**: Use Lakebridge's transpile command with Switch

For complete usage instructions and configuration options, refer to the [Lakebridge documentation](https://databrickslabs.github.io/lakebridge).
