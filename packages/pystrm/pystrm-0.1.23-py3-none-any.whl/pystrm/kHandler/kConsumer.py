import logging
from functools import lru_cache
from attrs import define, field
from json import dumps

from confluent_kafka import Consumer
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField
from pystrm.kHandler.kSchemaRegistry import KSR
from pystrm.kHandler.kUtils import get_clientSchema
from pystrm.utils.common.constants import Constants
from pystrm.utils.logger.logDecor import logtimer



logger = logging.getLogger(__name__)

@lru_cache
def schemaClient(topic: str, schema_type: str) -> KSR:

    schema_str = get_clientSchema(topic, schema_type=schema_type)
    schema_client = KSR(topic=topic, schema_str=dumps(schema_str), schema_type=schema_type)

    return schema_client


@define(kw_only=True)
class kConsume:
    topic: str = field(eq=str)
    groupId: str = field(eq=str, default=None)
    schema_type: str = field(eq=str, default=None)

    @logtimer
    def consume_message(self):

        consumer = Consumer({"bootstrap.servers": Constants.KAFKA_BROKERS.value, "group.id": self.groupId})
        consumer.subscribe([self.topic])

        try:
            while True:
                msg = consumer.poll(0.5)
                if msg is None:
                    continue
                if msg.error():
                    logger.error("Failed to recieve message. Error: %s" % (str(msg.error())))
                    continue
                logger.info("Message Consumed: %s" % (str(msg.value())))
        except KeyboardInterrupt:
            logger.warning("Keyboard Interrupt happened")
        finally:
            consumer.close()


    @logtimer
    def consume_serialized_message(self):

        consumer = Consumer({"bootstrap.servers": Constants.KAFKA_BROKERS.value, "group.id": self.groupId})
        consumer.subscribe([self.topic])
        schema_client = schemaClient(self.topic, self.schema_type)
        schema_str = schema_client.get_schema_str()
        value_deserializer = AvroDeserializer(schema_client, schema_str)

        try:
            while True:
                msg = consumer.poll(0.5)
                if msg is None:
                    continue
                if msg.error():
                    logger.error("Failed to recieve message. Error: %s" % (str(msg.error())))
                    continue
                # logger.info("Message Consumed: %s" % (str(msg.value())))
                message = msg.value()
                deserialized_message = value_deserializer(message, SerializationContext(self.topic, MessageField.VALUE))
                logger.info(f"Message Consumed: {deserialized_message}")
        except KeyboardInterrupt:
            logger.warning("Keyboard Interrupt happened")
        finally:
            consumer.close()
