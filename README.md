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

- Python 3.9+ (for local development)
- Docker and Docker Compose (for containerized setup)
- Cloudinary account (for file storage)

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd blog-be-fastapi
```

### 2. Configure environment variables

Create a `.env` file in the project root with the following variables. 

**Important**: Update these values, especially:
- `SECRET_KEY` - Generate a strong random key (use `openssl rand -hex 32` or similar)
- Cloudinary credentials (required for file uploads)
- MongoDB and Redis credentials (if not using Docker Compose defaults)

The `.env` file should contain:

```env
# ============================================
# MongoDB Configuration
# ============================================
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=password
MONGODB_DB_NAME=blog
MONGODB_DB_PORT=27017
# For local development (without Docker), use:
# MONGODB_URL=mongodb://admin:password@localhost:27017/blog?authSource=admin
# For Docker Compose, MONGODB_URL is auto-generated

# ============================================
# Redis Configuration
# ============================================
REDIS_HOST=localhost
# For Docker Compose, REDIS_HOST is automatically set to 'redis'
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# ============================================
# Application Configuration
# ============================================
API_V1_PREFIX=/api/v1
LOG_LEVEL=info
DEBUG=false
APP_PORT=8000
ENVIRONMENT=development

# ============================================
# JWT Authentication (REQUIRED)
# ============================================
# IMPORTANT: Change SECRET_KEY in production!
SECRET_KEY=your-secret-key-here-change-in-production-use-a-strong-random-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============================================
# CORS Configuration
# ============================================
# Comma-separated list of allowed origins (NO spaces, NO brackets)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:4200

# ============================================
# Public Routes (Optional)
# ============================================
# Comma-separated list of routes that don't require authentication
PUBLIC_ROUTES=/api/v1/auth/login,/api/v1/auth/register,/health,/

# ============================================
# Cloudinary Configuration (REQUIRED for file uploads)
# ============================================
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret
CLOUDINARY_CLOUD_FOLDER=blog

# ============================================
# File Upload Configuration
# ============================================
# Comma-separated list of allowed MIME types
ALLOWED_MIME_TYPES_STR=image/jpeg,image/png,image/gif,image/webp

# ============================================
# Default User (for development seeding)
# ============================================
# This user is created automatically if ENABLE_SEED_DATA=true
DEFAULT_USER_EMAIL=admin@example.com
DEFAULT_USER_PASSWORD=admin123
DEFAULT_USER_FULL_NAME=Admin User
DEFAULT_USER_ROLE=admin
DEFAULT_USER_DATE_OF_BIRTH=1990-01-01
ENABLE_SEED_DATA=true

# ============================================
# Rate Limiting
# ============================================
ENABLE_RATE_LIMITING=true

# ============================================
# Security Settings
# ============================================
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=15
```

**Important Notes**: 
- **Comma-separated strings**: `ALLOWED_ORIGINS`, `PUBLIC_ROUTES`, and `ALLOWED_MIME_TYPES_STR` must be comma-separated strings (NO spaces, NO brackets, NO quotes)
- **MONGODB_URL**: Automatically generated in Docker Compose. For local development, uncomment and set it manually
- **REDIS_HOST**: Set to `localhost` for local dev, automatically set to `redis` in Docker Compose
- **SECRET_KEY**: Must be changed in production! Use a strong, random key
- **Cloudinary**: Required for file upload functionality
- **ALLOWED_MIME_TYPES_STR**: Access it in code as `settings.ALLOWED_MIME_TYPES` (it's automatically converted to a set)

## 🐳 Running with Docker (Recommended)

### Quick Start with Docker Compose

The easiest way to run the entire application is using Docker Compose, which sets up all services (API, MongoDB, Redis) automatically:

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

This will start:
- **FastAPI Application** on port 8000 (or your configured `APP_PORT`)
- **MongoDB** on port 27017
- **Redis** on port 6379

The API will be available at: `http://localhost:8000`

### Docker Compose Services

The `docker-compose.yml` includes:
- **api**: FastAPI application with hot-reload enabled (source code is mounted)
- **mongodb**: MongoDB 7.0 with authentication
- **redis**: Redis 7.2 for caching and rate limiting

All services are connected via a Docker network and have health checks configured.

## 💻 Running Locally (Without Docker)

### 1. Start services with Docker Compose (MongoDB & Redis only)

If you want to run the API locally but use Docker for databases:

```bash
# Start only MongoDB and Redis
docker-compose up -d mongodb redis
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python -m src.main
```

Or with uvicorn directly:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Note**: When running locally, make sure your `.env` file has:
- `MONGODB_URL=mongodb://admin:password@localhost:27017/blog?authSource=admin`
- `REDIS_HOST=localhost`

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
├── Dockerfile               # Docker image definition
├── .dockerignore            # Files to exclude from Docker build
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

## 🐳 Docker Details

### Dockerfile

The project includes a `Dockerfile` that:
- Uses Python 3.11 slim base image
- Installs system dependencies and Python packages
- Exposes port 8000
- Runs the FastAPI application with uvicorn

### Build Docker image manually

```bash
docker build -t blog-api .
docker run -p 8000:8000 --env-file .env blog-api
```

### Docker Compose Configuration

The `docker-compose.yml` file includes:

- **Environment variable support**: Loads from `.env` file and provides defaults
- **Health checks**: MongoDB and Redis have health checks to ensure services are ready
- **Volume mounting**: Source code is mounted for hot-reload during development
- **Network isolation**: All services are on a dedicated Docker network
- **Automatic restarts**: API service restarts automatically unless stopped

### Environment Variables in Docker

The docker-compose.yml automatically:
- Loads variables from `.env` file
- Provides sensible defaults for development
- Configures MongoDB connection string for container networking
- Sets Redis host to use the service name

**Important**: Make sure to set `SECRET_KEY` and Cloudinary credentials in your `.env` file before running in production!

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

Configure allowed origins in the `.env` file as a comma-separated string:

```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:4200
```

The application automatically parses this into a list internally.

### Allowed MIME Types

Configure allowed MIME types for file uploads:

```env
ALLOWED_MIME_TYPES_STR=image/jpeg,image/png,image/gif,image/webp
```

This is automatically converted to a set in the application code.

## 📝 Notes

- The API uses MongoDB as the main database
- Redis is used for cache and rate limiting
- Files are stored in Cloudinary
- All endpoints (except public ones) require JWT authentication
- OpenAPI documentation is available at `/docs`
- Environment variables for lists (ALLOWED_ORIGINS, PUBLIC_ROUTES) should be comma-separated strings
- `ALLOWED_MIME_TYPES_STR` is used in environment variables, but accessed as `settings.ALLOWED_MIME_TYPES` (property)
- Docker Compose automatically handles service dependencies and health checks
- Source code is mounted as a volume in Docker for hot-reload during development

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
