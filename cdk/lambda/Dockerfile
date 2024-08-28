# Use the Amazon Linux 2 base image with Python 3.12
FROM public.ecr.aws/lambda/python:3.9-arm64

# Copy function code
COPY requirements.txt ${LAMBDA_TASK_ROOT}
COPY index.py ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "index.handler" ]