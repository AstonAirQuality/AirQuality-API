description = """
# Aston Air Quality API

Easily manage air quality sensors, users, and data ingestion logs with a modern RESTful API. 🚀

## Features

### Sensors
- **Create** new sensors
- **Read** sensor details
- **Update** sensor information
- **Delete** sensors

### Sensor Summaries
- **Read** sensor summary data

### Sensor Types
- **Create** sensor types
- **Read** sensor type details
- **Update** sensor types
- **Delete** sensor types

### Users
- **Create** users
- **Read** user information

### Logs
- **Read** ingestion logs
- **Delete** logs

### Authentication
- **Sign in**
- **Sign up**
- **Firebase login**
- **Firebase register**
- **Delete account**
"""

tags_metadata = [
    {
        "name": "auth",
        "description": "Endpoints for Firebase authentication and account management.",
    },
    {
        "name": "sensor",
        "description": "CRUD operations for air quality sensors.",
    },
    {
        "name": "sensor-type",
        "description": "Manage different types of sensors.",
    },
    {
        "name": "sensor-summary",
        "description": "Access summarized sensor data.",
    },
    {
        "name": "api-task",
        "description": "Background and scheduled API tasks.",
    },
    {
        "name": "user",
        "description": "User account operations.",
    },
    {
        "name": "data-ingestion-logs",
        "description": "View and manage data ingestion logs.",
    },
]
