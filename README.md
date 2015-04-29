# AWS Monocyte
[![Build Status](https://api.travis-ci.org/ImmobilienScout24/aws-monocyte.svg?branch=master)](https://travis-ci.org/ImmobilienScout24/aws-monocyte)
[![Coverage Status](https://coveralls.io/repos/ImmobilienScout24/aws-monocyte/badge.svg)](https://coveralls.io/r/ImmobilienScout24/aws-monocyte)
[![Codacy Badge](https://www.codacy.com/project/badge/ab632d7511e14a7ebfd47a797ced7b62)](https://www.codacy.com/public/jan_1691/aws-monocyte_2)

**Monocyte - Search and Destroy unwanted AWS Resources relentlessly.**
Monocyte is a bot for destroying AWS resources in non-EU regions written in Python using Boto.
It is especially useful for companies that are bound to European privacy laws and for that reason don't want to process user data in non-EU regions.

The name [Monocyte](https://en.wikipedia.org/wiki/Monocyte) is related to a type of white blood cells that are part of a human's innate immune system, the first line of defense being responsible for searching and destroying alien organisms to prevent unwanted infections.

## Background
With Ireland and Frankfurt being available as AWS regions nowadays, Amazon (more or less) extinguished 
EU and especially German legal concerns regarding storage and processing of privacy-related data.
However, for European companies it remains difficult to prevent (accidental) usage of services outside the EU, 
as there is still no standardized way to restrict AWS-account rights on this region-level.

Especially in open, DevOps-inspired company cultures like ours this becomes a major issue. 
On the one hand we want our teams to work with AWS and manage their own accounts mostly autonomously.
On the other hand we are bound to EU and German privacy laws and for that reason want to search and destroy 
unwanted AWS resources relentlessly. Therefore, we started implementing our own basic AWS immune system layer: Monocyte.

**Also read [AWS Monocyte - Let’s Build a Cloud Immune System](http://www.datahack.it/cloud-privacy-aws-monocyte/) or 
check out [the presentation](https://dl.dropboxusercontent.com/u/1874278/datahackit/AWS-Monocyte.pdf) we did for the AWS UserGroup Meetup in March 2015 at the Immobilien Scout HQ in Berlin.**

## Prerequisites
- [Boto SDK](http://docs.pythonboto.org/en/latest/getting_started.html)
- [AWS Credentials for Boto](http://docs.pythonboto.org/en/latest/boto_config_tut.html#credentials)

## Usage
```
pip install aws-monocyte
monocyte --help

usage:
    monocyte [options]

options:
    --dry-run=bool valid values "True" or "False" [default: True]
    --use-handlers=HANDLER1,HANDLER2,...    aws handlers to use (order might be important)
        [default: cloudformation.Stack, ec2.Instance, ec2.Volume, rds2.Instance, rds2.Snapshot, dynamodb.Table, s3.Bucket]
    --allowed-regions-prefixes=PREFIX1,PREFIX2,...  allowed regions start with these prefixes [default: eu]
    --ignored-regions=REGION1,REGION2,...  regions to be ignored [default: cn-north-1, us-gov-west-1]
    --ignored-resources=RESOURCE1,RESOURCE2,... resources to be ignored
        [default: cloudformation.cloudtrail-logging]
    --cwl-groupname=GROUPNAME  log events to CloudWatchLogs Group
```

## Licensing 
Monocyte is licensed under [Apache License, Version 2.0](https://github.com/ImmobilienScout24/aws-monocyte/blob/master/LICENSE.txt).
