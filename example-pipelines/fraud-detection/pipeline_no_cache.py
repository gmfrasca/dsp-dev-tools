# kfp imports
import kfp.dsl as dsl

# Component imports
from fetch_data import fetch_transactionsdb_data
from data_validation import validate_transactiondb_data
from data_preprocessing import preprocess_transactiondb_data
from train_model import train_fraud_model, convert_keras_to_onnx
from evaluate_model import evaluate_keras_model_performance, validate_onnx_model

data_connection_secret_name = 'aws-connection-models'

# Create pipeline
@dsl.pipeline(
  name='fraud-detection-training-pipeline',
  description='Trains the fraud detection model.',
)
def fraud_training_pipeline(datastore: dict, hyperparameters: dict):
    fetch_task = fetch_transactionsdb_data(datastore = datastore)

    # Validate Data
    data_validation_task = validate_transactiondb_data(dataset = fetch_task.outputs["dataset"]).set_caching_options(enable_caching=False)


    # Pre-process Data
    pre_processing_task = preprocess_transactiondb_data(in_data = fetch_task.outputs["dataset"]).set_caching_options(enable_caching=False)

    # Train Keras model
    training_task = train_fraud_model(
        train_data = pre_processing_task.outputs["train_data"], 
        val_data = pre_processing_task.outputs["val_data"],
        scaler = pre_processing_task.outputs["scaler"],
        class_weights = pre_processing_task.outputs["class_weights"],
        hyperparameters = hyperparameters,
    ).set_caching_options(enable_caching=False)

    # Convert Keras model to ONNX
    convert_task = convert_keras_to_onnx(keras_model = training_task.outputs["trained_model"]).set_caching_options(enable_caching=False)

    # Evaluate Keras model performance
    model_evaluation_task = evaluate_keras_model_performance(
        model = training_task.outputs["trained_model"],
        test_data = pre_processing_task.outputs["test_data"],
        scaler = pre_processing_task.outputs["scaler"],
        previous_model_metrics = {"accuracy":0.85},
    ).set_caching_options(enable_caching=False)

    # Validate that the Keras -> ONNX conversion was successful
    model_validation_task = validate_onnx_model(
        keras_model = training_task.outputs["trained_model"],
        onnx_model = convert_task.outputs["onnx_model"],
        test_data = pre_processing_task.outputs["test_data"]
    ).set_caching_options(enable_caching=False)