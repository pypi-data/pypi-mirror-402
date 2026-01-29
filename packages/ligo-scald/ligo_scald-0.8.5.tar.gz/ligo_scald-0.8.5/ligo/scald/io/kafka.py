from collections import namedtuple
import getpass
import json
import random
import string
import logging
from urllib.parse import urlparse

from confluent_kafka import Consumer, Producer

logger = logging.getLogger('scald')


Message = namedtuple("Message", "topic partition offset key value timestamp")


class Client(object):
    """A Kafka-based client to write and query time-based metrics.

    Parameters
    ----------
    uri : `str`
        the URI to connect to, of the form:
        kafka://[groupid@]hostname[:port][/topic1,topic2,...]

    """
    def __init__(self, uri):
        self.uri = uriparse(uri)

        ### kafka settings
        self._consumer_settings = {
            'bootstrap.servers': self.uri.broker,
            'group.id': self.uri.groupid,
        }
        self._producer_settings = {
            'bootstrap.servers': self.uri.broker,
            'message.max.bytes': 5242880,  # 5 MB
        }

        ### set up producer
        self._producer = Producer(self._producer_settings)

        ### set up consumer
        self._consumer = Consumer(self._consumer_settings)
        if self.uri.topics:
            self._consumer.subscribe([topic for topic in self.uri.topics])
        self.topics = self.uri.topics

    def subscribe(self, topic):
        """Subscribe to Kafka topics.

        Parameters
        ----------
        topic : `str` or `list`
            the topic(s) to subscribe to

        """
        if isinstance(topic, str):
            topic = [topic]
        new_topics = [t for t in topic if t not in self.topics]
        if new_topics:
            self._consumer.subscribe(new_topics)
            self.topics |= set(new_topics)

    def query(self, tags=None, timeout=0.2, max_messages=1000):
        """Query data from Kafka.

        Parameters
        ----------
        tags : `list`
            user-based tags to filter data by
        timeout : `float`
             timeout for requesting messages from a topic, default = 0.2s
        max_messages : `int`
             max number of messages to process per iteration, default = 1000

        """
        if not tags:
            tags = []
        tags = set(tags)
        for msg in self._consumer.consume(num_messages=max_messages, timeout=timeout):
            if msg and not msg.error():
                if msg.key():
                    key = msg.key().decode("utf-8").split(".")
                    msg_tags = set(key)
                else:
                    key = []
                    msg_tags = set()
                if not tags or tags.issubset(msg_tags):
                    yield Message(
                        msg.topic(),
                        msg.partition(),
                        msg.offset(),
                        tuple(key),
                        json.loads(msg.value().decode("utf-8")),
                        msg.timestamp()[1],
                    )

    def write(self, topic, data, tags=None):
        """Write data into Kafka.

        Parameters
        ----------
        topic : `str`
            the topic name
        data : `dict`
            the data to store
        tags : `list`
            user-based tags associated with the data

        """
        payload = json.dumps(data).encode("utf-8")
        if tags:
            if isinstance(tags, list):
                tags = ".".join(tags).encode("utf-8")
            self._producer.produce(topic=topic, key=tags, value=payload)
        else:
            self._producer.produce(topic=topic, value=payload, on_delivery=self._delivery_report)
        self._producer.poll(0)

    @staticmethod
    def _delivery_report(error, msg):
        """
        Handle response of each message produced.
        """
        if error is not None:
            logger.warning(f"Message delivery failed: {error}")

    def close(self):
        """Close the connection to the client.

        """
        self._producer.flush()
        self._consumer.unsubscribe()
        self._consumer.close()


KafkaURI = namedtuple('KafkaURI', 'groupid broker topics')

def uriparse(uri):
    """Parses a Kafka URI of the form:

       kafka://[groupid@]broker[,broker2[,...]]/topicspec[,topicspec[,...]]

    and returns a namedtuple to access properties by name:

        uri.groupid
        uri.broker
        uri.topics

    """
    uri = urlparse(uri)
    assert uri.scheme == 'kafka'

    if uri.username:
        groupid, broker = uri.netloc.split('@')
    else:
        groupid, broker = generate_groupid(), uri.netloc

    topics = uri.path.lstrip('/')
    if topics:
        topics = topics.split(',')
    else:
        topics = []

    return KafkaURI(groupid, broker, set(topics))


def generate_groupid():
    """Generate a random Kafka groupid

    """
    return '-'.join((getpass.getuser(), random_alphanum(10)))


def random_alphanum(n):
    """Generate a random alpha-numeric sequence of N characters.

    """
    alphanum = string.ascii_uppercase + string.digits
    return ''.join(random.SystemRandom().choice(alphanum) for _ in range(n))
