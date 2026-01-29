# RabbitMQ
EXCHANGE_NAME = ""

# Topic definitions
JOB_OFFERS_TOPIC = "Job.{ContextId}.{FunctionName}.{Version}.Offers"
JOB_COMMAND_TOPIC = "Job.{ContextId}.{FunctionName}.{Version}.{JobId}.Command"
JOB_STATUS_TOPIC = "Job.{ContextId}.{FunctionName}.{Version}.{JobId}.Reporting.Status"
JOB_RESULT_TOPIC = "Job.{ContextId}.{FunctionName}.{Version}.{JobId}.Reporting.Result"

# Queue parameters
WORKER_COMMAND_PARAMS = {}
JOB_COMMAND_PARAMS = {}
