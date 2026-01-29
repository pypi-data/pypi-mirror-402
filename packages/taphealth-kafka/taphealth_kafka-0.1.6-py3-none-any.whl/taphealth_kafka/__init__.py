from importlib.metadata import PackageNotFoundError, version

from .client import KafkaClient
from .consumer import KafkaConsumer
from .producer import KafkaProducer
from .topics import Topics

try:
    __version__ = version("taphealth-kafka")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    "KafkaClient",
    "KafkaConsumer",
    "KafkaProducer",
    "Topics",
    "__version__",
]
