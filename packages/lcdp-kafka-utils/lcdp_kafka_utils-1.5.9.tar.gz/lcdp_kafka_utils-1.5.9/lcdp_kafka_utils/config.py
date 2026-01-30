import os
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer, AvroSerializer

SERVICE_NAME = os.getenv('SERVICE_NAME')
HERMES_BROKER = os.getenv('HERMES_BROKER')
HERMES_USERNAME = os.getenv('HERMES_USERNAME')
HERMES_PASSWORD = os.getenv('HERMES_PASSWORD')
HERMES_SCHEMA_REGISTRY_URL = os.getenv('HERMES_SCHEMA_REGISTRY_URL')


def check_configuration():
    return HERMES_BROKER and HERMES_SCHEMA_REGISTRY_URL


def build_schema_registry_config():
    config = {
        'url': HERMES_SCHEMA_REGISTRY_URL,
    }

    if HERMES_USERNAME:
        config = {
            **config,
            **{
                'basic.auth.user.info': "{}:{}".format(HERMES_USERNAME, HERMES_PASSWORD)
            }
        }

    return config


def build_base_config():
    config = {
        'bootstrap.servers': HERMES_BROKER,
    }

    if HERMES_USERNAME:
        config = {
            **config,
            **{
                'security.protocol': 'SASL_SSL',
                'sasl.mechanism': 'SCRAM-SHA-512',
                'sasl.username': HERMES_USERNAME,
                'sasl.password': HERMES_PASSWORD,
            }
        }

    return config


def build_consumer_config(name, version):
    schema_registry_client = SchemaRegistryClient(
        build_schema_registry_config()
    )
    avro_deserializer = AvroDeserializer(schema_registry_client)

    # Compute GROUP_ID
    application_name = HERMES_USERNAME if HERMES_USERNAME else SERVICE_NAME
    group_id = "{}.{}.{}".format(application_name, name, version)

    return {
        **build_base_config(),
        **{
            'group.id': group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': 'false',
            'key.deserializer': avro_deserializer,
            'value.deserializer': avro_deserializer
        }
    }


def build_producer_config(key_schema_str, value_schema_str):
    schema_registry_client = SchemaRegistryClient(
        build_schema_registry_config()
    )
    avro_serializer_configuration = {"auto.register.schemas": True}
    key_serializer = AvroSerializer(schema_str=key_schema_str, schema_registry_client=schema_registry_client,
                                    conf=avro_serializer_configuration)
    value_serializer = AvroSerializer(schema_str=value_schema_str, schema_registry_client=schema_registry_client,
                                      conf=avro_serializer_configuration)

    return {
        **build_base_config(),
        **{
            'key.serializer': key_serializer,
            'value.serializer': value_serializer
        }
    }
