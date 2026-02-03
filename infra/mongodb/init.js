// Inicialización de MongoDB para Sales Service
db = db.getSiblingDB('sales_db');

// Crear colecciones con validación
db.createCollection('clients', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['business_name', 'rfc'],
      properties: {
        business_name: {
          bsonType: 'string',
          description: 'Nombre comercial requerido'
        },
        rfc: {
          bsonType: 'string',
          pattern: '^[A-Z]{3,4}[0-9]{6}[A-Z0-9]{3}$',
          description: 'RFC válido mexicano'
        }
      }
    }
  }
});

db.createCollection('orders', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['client_id', 'status', 'items'],
      properties: {
        status: {
          enum: ['DRAFT', 'PENDING_APPROVAL', 'CONFIRMED', 'IN_ROUTE', 'DELIVERED', 'CANCELLED']
        }
      }
    }
  }
});

// Índices para performance
db.clients.createIndex({ 'rfc': 1 }, { unique: true });
db.orders.createIndex({ 'client_id': 1, 'created_at': -1 });
db.orders.createIndex({ 'status': 1 });

print('MongoDB initialized successfully');
