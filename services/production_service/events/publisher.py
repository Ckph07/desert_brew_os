"""
RabbitMQ event publisher for Production Service.
"""
import pika
import json
from typing import Dict, Optional
from datetime import datetime


class EventPublisher:
    """RabbitMQ event publisher for production events."""
    
    def __init__(self, rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"):
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
    
    def connect(self):
        """Establish RabbitMQ connection and declare exchange."""
        if self.connection and self.connection.is_open:
            return
        
        self.connection = pika.BlockingConnection(
            pika.URLParameters(self.rabbitmq_url)
        )
        self.channel = self.connection.channel()
        
        # Declare production exchange (topic)
        self.channel.exchange_declare(
            exchange='production',
            exchange_type='topic',
            durable=True
        )
    
    def publish(
        self,
        routing_key: str,
        message: Dict,
        exchange: str = 'production'
    ):
        """
        Publish event to RabbitMQ.
        
        Args:
            routing_key: Event routing key (e.g., "production.batch_started")
            message: Event payload (will be JSON serialized)
            exchange: RabbitMQ exchange name
        """
        if not self.channel or not self.connection or not self.connection.is_open:
            self.connect()
        
        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = datetime.utcnow().isoformat()
        
        self.channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent
                content_type='application/json',
                timestamp=int(datetime.utcnow().timestamp())
            )
        )
    
    def close(self):
        """Close RabbitMQ connection."""
        if self.connection and self.connection.is_open:
            self.connection.close()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Dependency injection
def get_event_publisher() -> EventPublisher:
    """FastAPI dependency for EventPublisher."""
    publisher = EventPublisher()
    try:
        publisher.connect()
        yield publisher
    finally:
        publisher.close()
