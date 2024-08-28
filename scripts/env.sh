#!/bin/bash

export PROJECT_NAME="SingleStoreStreaming"
export AWS_ACCOUNT_ID=`aws sts get-caller-identity --query Account --output text`
export AWS_REGION=`aws configure get region`
export DATABASE_NAME="vehicle_db"
export DESTINATION_TABLE="vehicle_data"
