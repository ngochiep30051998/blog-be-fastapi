# Blog API - FastAPI Backend

REST API for a personal blog built with FastAPI, following Domain-Driven Design (DDD) principles and clean architecture.

## 🚀 Features

- **DDD Architecture**: Clear separation between domain, application, and infrastructure layers
- **JWT Authentication**: Token-based authentication system using JWT
- **Role-Based Access Control**: User roles (admin, writer, guest)
- **Rate Limiting**: Abuse protection with Redis
- **CORS Configured**: Support for multiple origins
- **File Management**: Cloudinary integration for image storage
- **MongoDB Database**: Data storage with MongoDB
- **Redis Cache**: Performance improvement with Redis
- **Auto Documentation**: Integrated Swagger/OpenAPI
- **Docker Compose**: Ready-to-use development setup

## 📋 Prerequisites

- Python 3.9+
- Docker and Docker Compose
- MongoDB (or use Docker Compose)
- Redis (or use Docker Compose)
- Cloudinary account (for file storage)

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd blog-be-fastapi
```

### 2. Configure environment variables

Create a `.env` file in the project root with the following variables:

```env
# MongoDB
MONGODB_URL=mongodb://admin:password@localhost:27017/
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=password
MONGODB_DB_NAME=blog
MONGODB_DB_PORT=27017

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Application
API_V1_PREFIX=/api/v1
LOG_LEVEL=INFO
DEBUG=True
APP_PORT=8000
ENVIRONMENT=development

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8080","http://localhost:4200"]

# Public Routes (no authentication required)
PUBLIC_ROUTES=["/api/v1/auth/login","/api/v1/auth/register","/health","/"]

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
CLOUDINARY_CLOUD_FOLDER=blog

# Allowed MIME Types
ALLOWED_MIME_TYPES={"image/jpeg", "image/png", "image/gif"}

# Default User (for development)
DEFAULT_USER_EMAIL=admin@example.com
DEFAULT_USER_PASSWORD=admin123
DEFAULT_USER_FULL_NAME=Admin User
DEFAULT_USER_ROLE=admin
DEFAULT_USER_DATE_OF_BIRTH=1990-01-01
ENABLE_SEED_DATA=True

# Rate Limiting
ENABLE_RATE_LIMITING=True

# Security
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=15
```

### 3. Start services with Docker Compose

```bash
docker-compose up -d
```

This will start:
- MongoDB on port 27017
- Redis on port 6379

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python -m src.main
```

Or with uvicorn directly:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: `http://localhost:8000`

## 📚 API Documentation

Once the application is running, you can access:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 🏗️ Project Structure

```
blog-be-fastapi/
├── src/
│   ├── application/          # Application layer
│   │   ├── dependencies/      # Dependencies (role checker, etc.)
│   │   ├── dto/              # Data Transfer Objects
│   │   └── services/         # Application services
│   ├── config/               # Configuration
│   │   └── settings.py       # Environment variables
│   ├── core/                 # Shared code
│   │   ├── constants.py
│   │   ├── role.py           # User roles
│   │   └── value_objects/    # Value objects
│   ├── domain/               # Domain layer (DDD)
│   │   ├── posts/           # Post entity
│   │   ├── categories/      # Category entity
│   │   ├── tags/            # Tag entity
│   │   ├── users/           # User entity
│   │   ├── auth/            # Authentication
│   │   └── files/           # File management
│   ├── infrastructure/       # Infrastructure layer
│   │   ├── cache/           # Redis cache
│   │   ├── middleware/      # Middlewares (auth, CORS, rate limiting)
│   │   └── mongo/           # MongoDB repository implementations
│   ├── tests/               # Tests
│   ├── utils/               # Utilities
│   └── main.py              # Entry point
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile               # Dockerfile (if applicable)
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## 🔐 Authentication

The API uses JWT authentication. To access protected endpoints:

1. **Login**: `POST /api/v1/auth/login`
   ```json
   {
     "email": "admin@example.com",
     "password": "admin123"
   }
   ```

2. **Use the token**: Include the token in the header:
   ```
   Authorization: Bearer <your-jwt-token>
   ```

## 👥 User Roles

- **admin**: Full access to all functionalities
- **writer**: Can create, edit, and publish posts
- **guest**: Read-only access

## 📡 Main Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/register` - Register user (admin only)
- `POST /api/v1/auth/logout` - Logout

### Posts
- `GET /api/v1/posts` - List posts (with pagination and filters)
- `GET /api/v1/posts/{post_id}` - Get post by ID
- `POST /api/v1/posts` - Create post (admin, writer, user)
- `PATCH /api/v1/posts/{post_id}` - Update post (admin, writer)
- `DELETE /api/v1/posts/{post_id}` - Delete post (admin, writer)
- `PATCH /api/v1/posts/{post_id}/publish` - Publish post (admin, writer)
- `PATCH /api/v1/posts/{post_id}/unpublish` - Unpublish post (admin, writer)

### Categories
- `GET /api/v1/categories` - List categories
- `POST /api/v1/categories` - Create category (admin)
- `PATCH /api/v1/categories/{category_id}` - Update category (admin)
- `DELETE /api/v1/categories/{category_id}` - Delete category (admin)

### Tags
- `GET /api/v1/tags` - List tags
- `POST /api/v1/tags` - Create tag (admin)
- `PATCH /api/v1/tags/{tag_id}` - Update tag (admin)
- `DELETE /api/v1/tags/{tag_id}` - Delete tag (admin)

### Users
- `GET /api/v1/users` - List users (admin)
- `GET /api/v1/users/{user_id}` - Get user (admin)
- `PATCH /api/v1/users/{user_id}` - Update user (admin)

### Files
- `POST /api/v1/files/upload` - Upload file (admin, writer)
- `DELETE /api/v1/files/{file_id}` - Delete file (admin, writer)

## 🔒 Security

- **Rate Limiting**: 40 requests per minute per IP (configurable)
- **Account Lockout**: After 5 failed login attempts, account is locked for 15 minutes
- **CORS**: Configured to allow only specific origins
- **Data Validation**: Automatic validation with Pydantic
- **Error Handling**: Consistent error responses with CORS headers

## 🧪 Development

### Run in development mode

```bash
uvicorn src.main:app --reload
```

### Data seeding

The system includes automatic seeding that runs when the application starts (if `ENABLE_SEED_DATA=True`). This creates a default user according to the environment variables.

## 🐳 Docker

### Build Docker image

```bash
docker build -t blog-api .
```

### Run with Docker Compose

```bash
docker-compose up -d
```

## 📦 Main Dependencies

- **FastAPI**: Modern and fast web framework
- **Uvicorn**: ASGI server
- **Motor**: Async driver for MongoDB
- **Pydantic**: Data validation
- **Redis**: Cache and rate limiting
- **python-jose**: JWT handling
- **bcrypt**: Password hashing
- **Cloudinary**: Cloud file storage

## 🔧 Advanced Configuration

### Rate Limiting

Rate limiting is enabled by default. You can disable it or adjust the limits in `src/main.py`:

```python
app.add_middleware(
    AsyncRedisRateLimiter,
    redis_client=redis_client,
    limit=40,      # max 40 requests
    window=60      # per 60 seconds
)
```

### CORS

Configure allowed origins in the `.env` file:

```env
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

## 📝 Notes

- The API uses MongoDB as the main database
- Redis is used for cache and rate limiting
- Files are stored in Cloudinary
- All endpoints (except public ones) require JWT authentication
- OpenAPI documentation is available at `/docs`

## 🤝 Contributing

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 👤 Author

Developed with ❤️ using FastAPI and DDD architecture.
