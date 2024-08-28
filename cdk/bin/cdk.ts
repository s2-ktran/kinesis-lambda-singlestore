#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { StreamingServiceSingleStoreStack } from '../lib/cdk-stack';

const app = new cdk.App();

const envVariables = {
	projectName: process.env["PROJECT_NAME"] ?? "",
	region: process.env["AWS_REGION"] ?? "",
	accountId: process.env["AWS_ACCOUNT_ID"] ?? "",
	dbEndpoint: process.env["DB_ENDPOINT"] ?? "",
	username: process.env["DB_USERNAME"] ?? "",
	password: process.env["DB_PASSWORD"] ?? "",
	databaseName: process.env["DATABASE_NAME"] ?? "",
	destinationTable: process.env["DESTINATION_TABLE"] ?? "",
	streamingService: process.env["STREAMING_SERVICE"] ?? "",
};

new StreamingServiceSingleStoreStack(app, 'StreamingServiceSingleStoreStack', { ...envVariables });