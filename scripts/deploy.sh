#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "Script directory: $SCRIPT_DIR"

echo "Setting environment variables configuration"
. $SCRIPT_DIR/env.sh

# Enter in dbEndpoint, username, and password
read -p "Enter the database endpoint: " DB_ENDPOINT
read -p "Enter the database username: " DB_USERNAME
read -sp "Enter the database password: " DB_PASSWORD

# Export the variables
export DB_ENDPOINT
export DB_USERNAME
export DB_PASSWORD

# Prompt the user to select between Kinesis and SQS
echo "Select the AWS streaming service to use:"
select service in "Kinesis" "SQS"; do
  case $service in
    Kinesis)
      echo "You selected Kinesis"
      export STREAMING_SERVICE="Kinesis"
      break
      ;;
    SQS)
      echo "You selected SQS"
      export STREAMING_SERVICE="SQS"
      break
      ;;
    (*)
      echo "Invalid option $REPLY"
      ;;
  esac
done

# Check for security group
echo "Checking for CDK Bootstrap in current $AWS_REGION..."
cfn=$(aws cloudformation describe-stacks \
    --query "Stacks[?StackName=='CDKToolkit'].StackName" \
    --region $AWS_REGION \
    --output text)
if [[ -z "$cfn" ]]; then
    cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION
fi

# Deploy CDK
echo "Launching CDK application..."
cd $SCRIPT_DIR/../cdk
npm ci
cdk synth
cdk deploy --all --require-approval never