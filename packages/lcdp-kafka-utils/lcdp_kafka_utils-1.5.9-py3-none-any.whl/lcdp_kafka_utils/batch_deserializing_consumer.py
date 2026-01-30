from confluent_kafka.cimpl import Consumer as _ConsumerImpl
from confluent_kafka.error import (ConsumeError,
                    KeyDeserializationError,
                    ValueDeserializationError)
from confluent_kafka.serialization import (SerializationContext,
                            MessageField)


class BatchDeserializingConsumer(_ConsumerImpl):

    def __init__(self, conf):
        conf_copy = conf.copy()
        self._key_deserializer = conf_copy.pop('key.deserializer', None)
        self._value_deserializer = conf_copy.pop('value.deserializer', None)
        super(BatchDeserializingConsumer, self).__init__(conf_copy)

    def consume(self, num_messages=1, timeout=-1):

        # consume num_messages messages
        records = super(BatchDeserializingConsumer, self).consume(num_messages, timeout)
        # contain all deserialized records
        deserialized_records = []

        for record in records:
            try:
                if record is None:
                    continue

                # deserialize the record
                deserialized_records.append(self.deserialize_record(record))

            except Exception as e:
                print("Error when deserializing record: {}".format(record), e)
                continue

        return deserialized_records

    def deserialize_record(self, record):

        if record.error() is not None:
            raise ConsumeError(record.error(), kafka_message=record)

        ctx = SerializationContext(record.topic(), MessageField.VALUE, record.headers())
        value = record.value()
        if self._value_deserializer is not None:
            try:
                value = self._value_deserializer(value, ctx)
            except Exception as se:
                raise ValueDeserializationError(exception=se, kafka_message=record)

        key = record.key()
        ctx.field = MessageField.KEY
        if self._key_deserializer is not None:
            try:
                key = self._key_deserializer(key, ctx)
            except Exception as se:
                raise KeyDeserializationError(exception=se, kafka_message=record)

        record.set_key(key)
        record.set_value(value)

        return record