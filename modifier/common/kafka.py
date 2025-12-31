import json
from kafka import KafkaProducer, KafkaConsumer

BOOTSTRAP = "kafka-svc.inspection-zone.svc.cluster.local:9092"

def get_producer():
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode(),
        # AJOUTER CETTE LIGNE :
        api_version=(3, 4, 0) 
    )

def get_consumer(topic, group_id):
    return KafkaConsumer(
        topic,
        bootstrap_servers=BOOTSTRAP,
        group_id=group_id,
        value_deserializer=lambda v: json.loads(v.decode()),
        auto_offset_reset="earliest",
        # AJOUTER CETTE LIGNE :
        api_version=(3, 4, 0)
    )
