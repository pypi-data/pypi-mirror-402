import logging
import threading
import time

from confluent_kafka.serializing_producer import SerializingProducer
from .config import check_configuration, build_consumer_config, build_producer_config
from .batch_deserializing_consumer import BatchDeserializingConsumer

from confluent_kafka import KafkaException

log = logging.getLogger(__name__)

CONSUMER_POLL_TIMEOUT = 10.0
DURATION_BEFORE_RESTART = 5.0
N_BATCH_RECORDS = 1000


def delivery_report(err, msg):
    """
    Reports the failure or success of a message delivery.
    Args:
        err (KafkaError): The error that occurred on None on success.
        msg (Message): The message that was produced or failed.
    Note:
        In the delivery report callback the Message.key() and Message.value()
        will be the binary format as encoded by any configured Serializers and
        not the same object that was passed to produce().
        If you wish to pass the original object(s) for key and value to delivery
        report callback we recommend a bound callback or lambda where you pass
        the objects along.
    """
    if err is not None:
        log.error("Delivery failed for record {}: {}".format(msg.key(), err))
        return
    log.debug('Record {} successfully produced to {} [{}] at offset {}'.format(
        msg.key(), msg.topic(), msg.partition(), msg.offset()))


class CdcDtoTransformer(object):

    def __init__(self, topic_in, topic_out):
        self.topic_in = topic_in
        self.topic_out = topic_out
        self.running = False

    def run(self):
        if not check_configuration():
            raise Exception(f"Missing environment variable to run Kafka")

        if not self.topic_in or not self.topic_out:
            raise Exception(f"Empty topic in/out for CDC to DTO transformer")

        # RUNNING CONSUMER FOR READING MESSAGE FROM THE KAFKA TOPIC
        t = threading.Thread(target=self.start_listener, name="Start kafka listener")
        t.daemon = True
        t.start()

    def start_listener(self):
        while True:
            try:
                self.__process_events()
            except Exception as ex:
                log.error("Exception occured in Kafka Events Processing Thread: {}", ex)
                # pause a bit before restart
                log.info("Going to restart in : {} seconds".format(DURATION_BEFORE_RESTART))
                time.sleep(DURATION_BEFORE_RESTART)
                pass

    def __process_events(self):
        try:
            self.running = True
            consumer = self.create_consumer()
            producer = self.create_producer()

            while self.running:
                try:
                    # read N_MESSAGE_BATCH messages at the same time
                    records = consumer.consume(N_BATCH_RECORDS, CONSUMER_POLL_TIMEOUT)

                except KafkaException as ex:
                    # Ignore the exception like TOPIC_NOT_FOUND, PARTITTION_NOT_FOUND
                    log.error("CdcDtoTransformer exception", ex)
                    continue


                for record in records:

                    if record is None:
                        # There is no new record in the topic, do nothing
                        continue

                    if record.error():
                        print("Error reading message : {}".format(record.error()))
                        continue

                    if record.key() is None:
                        log.error("MUST FIX - Strange null key processed with value : {}".format(record.value()))
                        continue

                    if record.value() is None:
                        # Debezium by default generates a tombstone record to enable Kafka compaction after a delete record was generated.
                        # This record is usually filtered out to avoid duplicates as a delete record is converted to a tombstone record, too
                        continue

                    # 'after' can be null if ressource deleted or in case of update with capture.mode <> change_streams_update_full (default since 1.8.0.Alpha1)
                    # In this situation, just publish an event in the topic with null value
                    cdc_value = record.value().get('after', None)
                    cdc_key = record.key()

                    dto_value = self.build_value(cdc_value)
                    dto_key = self.build_key(cdc_key)

                    producer.produce(topic=self.topic_out,
                                     key=dto_key.dict() if dto_key else None,
                                     value=dto_value.dict() if dto_value else None,
                                     on_delivery=delivery_report)

                # Flush all message and commit after produce batch records
                producer.flush()
                consumer.commit(asynchronous=True)
        finally:
            if consumer:
                log.info("closing consumer")
                consumer.close()

            if producer:
                log.info("Flushing records...")
                producer.flush()

    def build_key(self, msg):
        raise NotImplementedError("Please Implement this method")

    def build_value(self, msg):
        raise NotImplementedError("Please Implement this method")

    def get_key_schema(self):
        raise NotImplementedError("Please Implement this method")

    def get_value_schema(self):
        raise NotImplementedError("Please Implement this method")

    def get_name(self):
        raise NotImplementedError("Please Implement this method")

    def get_version(self):
        raise NotImplementedError("Please Implement this method")

    def create_producer(self):
        config = build_producer_config(self.get_key_schema(), self.get_value_schema())
        batch_producer = SerializingProducer(config)
        return batch_producer

    def create_consumer(self):
        config = build_consumer_config(self.get_name(), self.get_version())
        batch_consumer = BatchDeserializingConsumer(config)
        batch_consumer.subscribe([self.topic_in])
        return batch_consumer

    def shutdown(self):
        self.running = False
