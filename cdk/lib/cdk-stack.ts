import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as path from 'path';

export interface StreamingServiceSingleStoreStackProps extends cdk.StackProps {
  projectName: string;
  region: string;
	accountId: string;
  dbEndpoint: string;
  username: string;
  password: string;
  databaseName: string;
  destinationTable: string;
  streamingService: string;
}

export class StreamingServiceSingleStoreStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: StreamingServiceSingleStoreStackProps) {
    super(scope, id, props);

    const { 
      projectName, 
      region, 
      accountId, 
      dbEndpoint, 
      username, 
      password, 
      databaseName, 
      destinationTable,
      streamingService,
    } = props;

    // Create a VPC with public and private subnets
    const vpc = new cdk.aws_ec2.Vpc(this, 'LambdaVpc', {
      vpcName: `${projectName}-${accountId}-vpc`,
      maxAzs: 1,
      subnetConfiguration: [
        {
          subnetType: cdk.aws_ec2.SubnetType.PRIVATE_WITH_EGRESS,
          name: 'PrivateSubnet',
        },
        {
          subnetType: cdk.aws_ec2.SubnetType.PUBLIC,
          name: 'PublicSubnet',
        },
      ],
    });
    const privateSubnet = vpc.selectSubnets({ subnetType: cdk.aws_ec2.SubnetType.PRIVATE_WITH_EGRESS }).subnets[0];


    
    // Secrets Manager
    const dbCredentialsSecret = new cdk.aws_secretsmanager.Secret(this, 'DBCredentialsSecret', {
      secretName: `${projectName}-${accountId}-secret`,
      generateSecretString: {
        secretStringTemplate: JSON.stringify({
          DB_USERNAME: username,
          PASSWORD: password,
          ENDPOINT: dbEndpoint,
          DATABASE_NAME: databaseName,
          DESTINATION_TABLE: destinationTable
        }),
        generateStringKey: projectName,
        excludePunctuation: true,
      },
    });

    // Lambda function
    const lambdaSecurityGroup = new cdk.aws_ec2.SecurityGroup(this, 'LambdaSG', {
      vpc,
      allowAllOutbound: true,
    });

    const lambdaFunction = new cdk.aws_lambda.DockerImageFunction(this, 'ProcessorFunction', {
      functionName: `${projectName}-${accountId}-processor`,
      code: cdk.aws_lambda.DockerImageCode.fromImageAsset(path.join(__dirname, '../lambda')),
      architecture: cdk.aws_lambda.Architecture.ARM_64,
      timeout: cdk.Duration.seconds(30),
      memorySize: 3008, // Max memory size of 10 GB
      vpc,
      vpcSubnets: {
        subnets: [privateSubnet], // Use the specific subnet
      },
      securityGroups: [lambdaSecurityGroup],
      environment: {
        SECRET_NAME: dbCredentialsSecret.secretName,
        REGION: region,
        SERVICE: streamingService,
      },
    });
    dbCredentialsSecret.grantRead(lambdaFunction);
    
    if (streamingService === "Kinesis") { 
      const stream = new cdk.aws_kinesis.Stream(this, 'KinesisStream', {
        streamName: `${projectName}-${accountId}-stream`,
        shardCount: 1,
      });  
      stream.grantRead(lambdaFunction);
      stream.applyRemovalPolicy(cdk.RemovalPolicy.DESTROY);

      lambdaFunction.addEventSource(new cdk.aws_lambda_event_sources.KinesisEventSource(stream, {
        startingPosition: cdk.aws_lambda.StartingPosition.TRIM_HORIZON,
        batchSize: 10,
      }));

      new cdk.aws_ec2.InterfaceVpcEndpoint(this, 'KinesisVpcEndpoint', {
        vpc,
        service: cdk.aws_ec2.InterfaceVpcEndpointAwsService.KINESIS_STREAMS,
        subnets: {
          subnets: [privateSubnet],
        },
        privateDnsEnabled: true,
      });  

      new cdk.CfnOutput(this, 'KinesisStreamArn', {
        value: stream.streamArn,
        description: 'The ARN of the Kinesis Data Stream',
      });

    } else if (streamingService === 'SQS') {
      const queue = new cdk.aws_sqs.Queue(this, 'SqsQueue', {
        queueName: `${projectName}-${accountId}-queue`,
        visibilityTimeout: cdk.Duration.seconds(30),
        retentionPeriod: cdk.Duration.days(4),
      });

      queue.grantConsumeMessages(lambdaFunction);

      lambdaFunction.addEventSource(new cdk.aws_lambda_event_sources.SqsEventSource(queue, {
        batchSize: 10,
      }));
      
      new cdk.CfnOutput(this, 'SQSQueueArn', {
        value: queue.queueArn,
        description: 'The ARN of the SQS Queue',
      });
    }

    // CDK Outputs
    new cdk.CfnOutput(this, 'StreamingService', {
      value: streamingService,
      description: 'The name of the streaming service used.',
    });

    new cdk.CfnOutput(this, 'LambdaFunctionArn', {
      value: lambdaFunction.functionArn,
      description: 'The ARN of the Lambda function',
    });

    new cdk.CfnOutput(this, 'VpcId', { 
      value: vpc.vpcId, 
      description: "VPC Id"
    });
  }
}
