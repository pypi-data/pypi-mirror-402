Datazone Client Library 👋

## Installation

You can install package via pip

```shell
pip install datazone
```

## Configuration & Login

Run the following command in your terminal to create a new profile.

```shell
datazone profile create
```

When prompted, enter the following information:

```shell
Profile Name: <PROFILE_NAME>
Host [app.datazone.co]: <DATAZONE_ADDRESS>
API Key: <API Key>
```

Then you can run following command to test it. (At the first profile creation, it will test automatically)

```shell
datazone auth test
```

## Create first repository

```shell
datazone repository create hello-world
cd hello-world
```

It creates a new folder in your current directory. Thıs folder has two file initially. `config.yaml` and `first_pipeline.py`.
After you modify your script you can deploy project via following command.

```shell
datazone repository deploy
```

After the deployment is complete, you can check your repository status via following command.

```shell
datazone repository summary
```

If repository has deployed, you can run your first execution with following command.

```shell
datazone execution run <pipeline_id>
```

## Commands

Also you can check all command with help sub command. `datazone auth --help` or `datazone repository summary --help`

```shell
# Auth
datazone auth test

# Profile
datazone profile list
datazone profile create
datazone profile delete <profile_name>
datazone profile setdefault <profile_name>

# Repository
datazone repository list
datazone repository create
datazone repository deploy
datazone repository summary <file_name>
datazone repository clone <repository_id>
datazone repository pull

# Dataset
datazone dataset list
datazone dataset show <dataset_id> [--size <n>] [--transaction-id <id>] [--query "<SQL>"]
datazone dataset transactions <dataset_id>

# Source
datazone source create
datazone source list
datazone source update <source_id>
datazone source delete <source_id>

# Extract
datazone extract create
datazone extract list
datazone extract update <extract_id>
datazone extract delete <extract_id>
datazone extract execute <extract_id>

# Schedule
datazone schedule create
datazone schedule list
datazone schedule delete <source_id>

# Execution
datazone execution run [--extract-id] [--pipeline-id] [<execution_type>] [<transform_selection>]
datazone execution list [--extract-id] [--pipeline-id]
datazone execution log <execution_id>

# Pipeline
datazone pipeline create
datazone pipeline list
datazone pipeline delete <pipeline_id>

# View
datazone view create
datazone view list [--dataset-id <dataset_id>]
datazone view delete <view_id>

# SQL
datazone sql <dataset_id> "<QUERY>" [--transaction-id <id>] [--size <n>]

# Project
datazone project activities list <project_id>

# Common
datazone version
datazone info
```
