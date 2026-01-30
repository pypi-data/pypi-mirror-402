import logging
import threading
import time

from confluent_kafka import KafkaException
from .config import check_configuration, build_consumer_config
from .batch_deserializing_consumer import BatchDeserializingConsumer

log = logging.getLogger(__name__)

CONSUMER_POLL_TIMEOUT = 10.0
DURATION_BEFORE_RESTART = 5.0
N_BATCH_RECORDS = 1000


class DtoActionExecute(object):

    def __init__(self, topic_in):
        self.topic_in = topic_in
        self.running = False

    def run(self):
        if not check_configuration():
            raise Exception(f"Missing environment variable to run Kafka")

        if not self.topic_in:
            raise Exception(f"Empty topic in for DTO")

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

            while self.running:
                try:
                    # read N_MESSAGE_BATCH messages at the same time
                    records = consumer.consume(N_BATCH_RECORDS, CONSUMER_POLL_TIMEOUT)


                except KafkaException as ex:
                    # Ignore the exception like TOPIC_NOT_FOUND, PARTITTION_NOT_FOUND
                    log.error("DtoActionExecute exception", ex)
                    continue

                if records:
                    self.action_events(records)

                consumer.commit(asynchronous=True)

        finally:
            if consumer:
                log.info("closing consumer")
                consumer.close()

    def action_events(self, records):
        raise NotImplementedError("Please Implement this method")

    def get_name(self):
        raise NotImplementedError("Please Implement this method")

    def get_version(self):
        raise NotImplementedError("Please Implement this method")

    def create_consumer(self):
        config = build_consumer_config(self.get_name(), self.get_version())
        batch_consumer = BatchDeserializingConsumer(config)
        batch_consumer.subscribe([self.topic_in])
        return batch_consumer

    def shutdown(self):
        self.running = False

    @staticmethod
    def dedupe(records):
        unique_keys = []
        deduped_records = []
        for record in list(reversed(records)):
            if record.key() not in unique_keys:
                deduped_records.append(record)
                unique_keys.append(record.key())

        return list(reversed(deduped_records))
