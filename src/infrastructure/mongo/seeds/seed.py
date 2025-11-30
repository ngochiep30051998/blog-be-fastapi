from bson import ObjectId
from typing import List
from datetime import datetime, timezone

from src.application.services.user_service import UserService
from src.application.services.category_service import CategoryService
from src.application.services.tag_service import TagService
from src.application.services.post_service import PostService
from src.config import settings
from src.domain.users.entity import UserEntity
from src.infrastructure.mongo.user_repository_impl import MongoUserRepository
from src.infrastructure.mongo.category_repository_impl import MongoCategoryRepository
from src.infrastructure.mongo.tag_repository_impl import MongoTagRepository
from src.infrastructure.mongo.post_repository_impl import MongoPostRepository
from src.infrastructure.mongo.database import get_database

class MongoSeeder:
    def __init__(self, user_service: UserService, category_service: CategoryService, 
                 tag_service: TagService, post_service: PostService):
        self.user_service = user_service
        self.category_service = category_service
        self.tag_service = tag_service
        self.post_service = post_service

    async def seed_users(self, users: List[dict]):
        for user in users:
            existing = await self.user_service.get_by_email(user["email"])
            if not existing:
                await self.user_service.register_user(
                    email=user["email"],
                    full_name=user["username"],
                    password=user["password"],
                    role=user["role"], 
                    date_of_birth=user["date_of_birth"]
                )

    async def seed_categories(self):
        """Seed 10 categories"""
        categories_data = [
            {"name": "Web Development", "description": "Articles about web development technologies and frameworks", "slug": "web-development"},
            {"name": "Python", "description": "Python programming tutorials and tips", "slug": "python"},
            {"name": "JavaScript", "description": "JavaScript and modern JS frameworks", "slug": "javascript"},
            {"name": "DevOps", "description": "DevOps practices, tools, and methodologies", "slug": "devops"},
            {"name": "Database", "description": "Database design, optimization, and management", "slug": "database"},
            {"name": "Mobile Development", "description": "Mobile app development for iOS and Android", "slug": "mobile-development"},
            {"name": "Cloud Computing", "description": "Cloud platforms and services", "slug": "cloud-computing"},
            {"name": "Machine Learning", "description": "AI and machine learning concepts and implementations", "slug": "machine-learning"},
            {"name": "Security", "description": "Cybersecurity and application security best practices", "slug": "security"},
            {"name": "Tutorials", "description": "Step-by-step tutorials and guides", "slug": "tutorials"},
        ]
        
        category_ids = {}
        for cat_data in categories_data:
            try:
                # Check if category exists by slug
                existing = await self.category_service.category_repo.collection.find_one({"slug": cat_data["slug"], "deleted_at": None})
                if existing:
                    category_ids[cat_data["name"]] = str(existing["_id"])
                    print(f"Category '{cat_data['name']}' already exists, skipping...")
                else:
                    category = await self.category_service.create_category(
                        name=cat_data["name"],
                        description=cat_data["description"],
                        slug_str=cat_data["slug"]
                    )
                    category_ids[cat_data["name"]] = str(category["_id"])
                    print(f"Created category: {cat_data['name']}")
            except Exception as e:
                print(f"Error creating category {cat_data['name']}: {e}")
        
        return category_ids

    async def seed_tags(self):
        """Seed 10 tags"""
        tags_data = [
            {"name": "FastAPI", "description": "FastAPI framework"},
            {"name": "React", "description": "React library for building user interfaces"},
            {"name": "Docker", "description": "Containerization platform"},
            {"name": "MongoDB", "description": "NoSQL database"},
            {"name": "REST API", "description": "RESTful API design"},
            {"name": "TypeScript", "description": "Typed superset of JavaScript"},
            {"name": "AWS", "description": "Amazon Web Services"},
            {"name": "Testing", "description": "Software testing practices"},
            {"name": "Best Practices", "description": "Coding and development best practices"},
            {"name": "Performance", "description": "Performance optimization"},
        ]
        
        tag_ids = {}
        for tag_data in tags_data:
            try:
                # Check if tag exists by name
                existing = await self.tag_service.tag_repo.get_by_name(tag_data["name"])
                if existing:
                    tag_ids[tag_data["name"]] = str(existing["_id"])
                    print(f"Tag '{tag_data['name']}' already exists, skipping...")
                else:
                    tag = await self.tag_service.create_tag(
                        name=tag_data["name"],
                        description=tag_data["description"]
                    )
                    tag_ids[tag_data["name"]] = str(tag["_id"])
                    print(f"Created tag: {tag_data['name']}")
            except Exception as e:
                print(f"Error creating tag {tag_data['name']}: {e}")
        
        return tag_ids

    async def seed_posts(self, user_id: str, category_ids: dict, tag_ids: dict):
        """Seed 20 published posts"""
        posts_data = [
            {
                "title": "Getting Started with FastAPI",
                "slug": "getting-started-with-fastapi",
                "excerpt": "Learn how to build modern APIs with FastAPI, a high-performance Python web framework.",
                "content": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints. In this comprehensive guide, we'll explore how to get started with FastAPI, set up your first project, and build a RESTful API.\n\n## Installation\n\nFirst, install FastAPI and Uvicorn:\n```bash\npip install fastapi uvicorn\n```\n\n## Creating Your First API\n\nLet's create a simple API endpoint:\n```python\nfrom fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get(\"/\")\ndef read_root():\n    return {\"Hello\": \"World\"}\n```\n\n## Running the Server\n\nStart your server with:\n```bash\nuvicorn main:app --reload\n```\n\nFastAPI automatically generates interactive API documentation at `/docs` and `/redoc`.",
                "category": "Python",
                "tags": ["FastAPI", "REST API"],
                "meta_title": "Getting Started with FastAPI - Complete Guide",
                "meta_description": "Learn how to build modern APIs with FastAPI. Complete tutorial with examples and best practices."
            },
            {
                "title": "Building RESTful APIs: Best Practices",
                "slug": "building-restful-apis-best-practices",
                "excerpt": "Discover the essential best practices for designing and implementing RESTful APIs that are scalable and maintainable.",
                "content": "RESTful APIs are the backbone of modern web applications. In this article, we'll explore best practices for designing and implementing RESTful APIs that are scalable, maintainable, and developer-friendly.\n\n## Use Proper HTTP Methods\n\n- GET: Retrieve resources\n- POST: Create new resources\n- PUT: Update entire resources\n- PATCH: Partial updates\n- DELETE: Remove resources\n\n## Consistent Naming Conventions\n\nUse plural nouns for resource names:\n- `/api/users` (not `/api/user`)\n- `/api/posts` (not `/api/post`)\n\n## Versioning\n\nAlways version your APIs:\n- `/api/v1/users`\n- `/api/v2/users`\n\n## Error Handling\n\nReturn appropriate HTTP status codes and consistent error formats.",
                "category": "Web Development",
                "tags": ["REST API", "Best Practices"],
                "meta_title": "RESTful API Best Practices Guide"
            },
            {
                "title": "React Hooks: A Complete Guide",
                "slug": "react-hooks-complete-guide",
                "excerpt": "Master React Hooks with this comprehensive guide covering useState, useEffect, and custom hooks.",
                "content": "React Hooks revolutionized how we write React components. Introduced in React 16.8, hooks allow you to use state and other React features without writing a class.\n\n## useState Hook\n\nThe useState hook lets you add state to functional components:\n```javascript\nimport { useState } from 'react';\n\nfunction Counter() {\n  const [count, setCount] = useState(0);\n  return (\n    <div>\n      <p>You clicked {count} times</p>\n      <button onClick={() => setCount(count + 1)}>Click me</button>\n    </div>\n  );\n}\n```\n\n## useEffect Hook\n\nuseEffect lets you perform side effects in functional components:\n```javascript\nuseEffect(() => {\n  document.title = `You clicked ${count} times`;\n}, [count]);\n```\n\n## Custom Hooks\n\nYou can create custom hooks to share stateful logic between components.",
                "category": "JavaScript",
                "tags": ["React", "JavaScript", "Best Practices"]
            },
            {
                "title": "Docker Containerization: From Basics to Production",
                "slug": "docker-containerization-basics-production",
                "excerpt": "Learn Docker from the ground up and deploy containerized applications to production.",
                "content": "Docker has become the standard for containerization in modern software development. This guide will take you from Docker basics to production deployment.\n\n## What is Docker?\n\nDocker is a platform for developing, shipping, and running applications in containers. Containers package an application with all its dependencies.\n\n## Basic Docker Commands\n\n```bash\n# Build an image\ndocker build -t myapp .\n\n# Run a container\ndocker run -p 3000:3000 myapp\n\n# List containers\ndocker ps\n\n# View logs\ndocker logs <container_id>\n```\n\n## Dockerfile Best Practices\n\n- Use multi-stage builds\n- Minimize layers\n- Use .dockerignore\n- Don't run as root\n\n## Docker Compose\n\nDocker Compose allows you to define and run multi-container applications.",
                "category": "DevOps",
                "tags": ["Docker", "DevOps", "Best Practices"]
            },
            {
                "title": "MongoDB Aggregation Pipeline Explained",
                "slug": "mongodb-aggregation-pipeline-explained",
                "excerpt": "Master MongoDB's powerful aggregation framework with practical examples and use cases.",
                "content": "MongoDB's aggregation pipeline is a powerful framework for data processing. It allows you to transform and combine documents from a collection.\n\n## Pipeline Stages\n\nThe aggregation pipeline consists of stages:\n- $match: Filter documents\n- $group: Group documents\n- $sort: Sort documents\n- $project: Reshape documents\n- $lookup: Join collections\n\n## Example\n\n```javascript\ndb.orders.aggregate([\n  { $match: { status: \"completed\" } },\n  { $group: { _id: \"$customer\", total: { $sum: \"$amount\" } } },\n  { $sort: { total: -1 } }\n])\n```\n\n## Performance Tips\n\n- Use indexes\n- Filter early with $match\n- Limit results\n- Use $project to reduce data",
                "category": "Database",
                "tags": ["MongoDB", "Database", "Best Practices"]
            },
            {
                "title": "TypeScript: Type Safety in JavaScript",
                "slug": "typescript-type-safety-javascript",
                "excerpt": "Discover how TypeScript brings type safety to JavaScript development.",
                "content": "TypeScript is a typed superset of JavaScript that compiles to plain JavaScript. It adds static type definitions to JavaScript.\n\n## Why TypeScript?\n\n- Catch errors early\n- Better IDE support\n- Improved code documentation\n- Easier refactoring\n\n## Basic Types\n\n```typescript\nlet name: string = \"John\";\nlet age: number = 30;\nlet isActive: boolean = true;\nlet items: string[] = [\"apple\", \"banana\"];\n```\n\n## Interfaces\n\n```typescript\ninterface User {\n  id: number;\n  name: string;\n  email?: string;\n}\n\nconst user: User = {\n  id: 1,\n  name: \"John\"\n};\n```\n\n## Generics\n\nTypeScript generics allow you to create reusable components.",
                "category": "JavaScript",
                "tags": ["TypeScript", "JavaScript", "Best Practices"]
            },
            {
                "title": "AWS Cloud Services Overview",
                "slug": "aws-cloud-services-overview",
                "excerpt": "An introduction to Amazon Web Services and its key services for developers.",
                "content": "Amazon Web Services (AWS) is a comprehensive cloud computing platform offering over 200 services. This article provides an overview of key AWS services.\n\n## Core Services\n\n### EC2 (Elastic Compute Cloud)\nVirtual servers in the cloud.\n\n### S3 (Simple Storage Service)\nObject storage for files and data.\n\n### RDS (Relational Database Service)\nManaged database service.\n\n### Lambda\nServerless compute service.\n\n## Getting Started\n\n1. Create an AWS account\n2. Set up IAM users\n3. Configure AWS CLI\n4. Deploy your first service\n\n## Best Practices\n\n- Use IAM roles\n- Enable CloudTrail\n- Set up billing alerts\n- Use multiple availability zones",
                "category": "Cloud Computing",
                "tags": ["AWS", "Cloud Computing", "Best Practices"]
            },
            {
                "title": "Testing Strategies for Modern Applications",
                "slug": "testing-strategies-modern-applications",
                "excerpt": "Learn effective testing strategies including unit, integration, and end-to-end testing.",
                "content": "Testing is crucial for maintaining code quality and preventing bugs. This guide covers different testing strategies.\n\n## Types of Tests\n\n### Unit Tests\nTest individual components in isolation.\n\n### Integration Tests\nTest how components work together.\n\n### E2E Tests\nTest the entire application flow.\n\n## Testing Pyramid\n\n- Many unit tests (base)\n- Some integration tests (middle)\n- Few E2E tests (top)\n\n## Tools\n\n- Jest for JavaScript\n- Pytest for Python\n- Cypress for E2E\n\n## Best Practices\n\n- Write tests first (TDD)\n- Keep tests independent\n- Use mocks sparingly\n- Test edge cases",
                "category": "Tutorials",
                "tags": ["Testing", "Best Practices", "Performance"]
            },
            {
                "title": "Performance Optimization Techniques",
                "slug": "performance-optimization-techniques",
                "excerpt": "Essential techniques to improve application performance and user experience.",
                "content": "Performance optimization is critical for user experience. This article covers key optimization techniques.\n\n## Frontend Optimization\n\n- Code splitting\n- Lazy loading\n- Image optimization\n- Caching strategies\n\n## Backend Optimization\n\n- Database indexing\n- Query optimization\n- Caching layers\n- Connection pooling\n\n## Monitoring\n\n- Use APM tools\n- Monitor key metrics\n- Set up alerts\n- Regular profiling\n\n## Tools\n\n- Lighthouse for web performance\n- New Relic for APM\n- Redis for caching",
                "category": "Web Development",
                "tags": ["Performance", "Best Practices"]
            },
            {
                "title": "Security Best Practices for Web Applications",
                "slug": "security-best-practices-web-applications",
                "excerpt": "Essential security practices to protect your web applications from common vulnerabilities.",
                "content": "Security is paramount in web development. This guide covers essential security practices.\n\n## Common Vulnerabilities\n\n- SQL Injection\n- XSS (Cross-Site Scripting)\n- CSRF (Cross-Site Request Forgery)\n- Authentication flaws\n\n## Best Practices\n\n### Input Validation\nAlways validate and sanitize user input.\n\n### Authentication\n- Use strong passwords\n- Implement 2FA\n- Secure session management\n\n### HTTPS\nAlways use HTTPS in production.\n\n### Dependency Management\nKeep dependencies updated and scan for vulnerabilities.\n\n## Tools\n\n- OWASP ZAP for security testing\n- Snyk for dependency scanning\n- Helmet.js for Express security",
                "category": "Security",
                "tags": ["Best Practices"]
            },
            {
                "title": "Introduction to Machine Learning",
                "slug": "introduction-machine-learning",
                "excerpt": "A beginner-friendly introduction to machine learning concepts and applications.",
                "content": "Machine Learning is transforming industries. This article provides an introduction to ML concepts.\n\n## What is Machine Learning?\n\nMachine Learning enables computers to learn from data without explicit programming.\n\n## Types of Learning\n\n### Supervised Learning\nLearning with labeled data.\n\n### Unsupervised Learning\nFinding patterns in unlabeled data.\n\n### Reinforcement Learning\nLearning through interaction and rewards.\n\n## Common Algorithms\n\n- Linear Regression\n- Decision Trees\n- Neural Networks\n- K-Means Clustering\n\n## Getting Started\n\n- Learn Python\n- Study mathematics (linear algebra, statistics)\n- Practice with datasets\n- Use libraries like scikit-learn",
                "category": "Machine Learning",
                "tags": ["Best Practices"]
            },
            {
                "title": "Mobile App Development: React Native vs Flutter",
                "slug": "mobile-app-development-react-native-vs-flutter",
                "excerpt": "Compare React Native and Flutter to choose the right framework for your mobile app project.",
                "content": "Choosing between React Native and Flutter is a common dilemma. This article compares both frameworks.\n\n## React Native\n\n### Pros\n- Large community\n- JavaScript/TypeScript\n- Hot reload\n- Native performance\n\n### Cons\n- Platform-specific code needed\n- Larger app size\n\n## Flutter\n\n### Pros\n- Single codebase\n- Fast performance\n- Beautiful UI\n- Strong typing (Dart)\n\n### Cons\n- Smaller community\n- Newer ecosystem\n\n## When to Choose What?\n\n- React Native: If you know JavaScript\n- Flutter: If you want consistent UI across platforms",
                "category": "Mobile Development",
                "tags": ["React", "Mobile Development", "Best Practices"]
            },
            {
                "title": "Building Scalable Microservices Architecture",
                "slug": "building-scalable-microservices-architecture",
                "excerpt": "Learn how to design and implement scalable microservices architectures.",
                "content": "Microservices architecture breaks applications into small, independent services. This guide covers best practices.\n\n## Benefits\n\n- Independent deployment\n- Technology diversity\n- Scalability\n- Fault isolation\n\n## Challenges\n\n- Service communication\n- Data consistency\n- Distributed tracing\n- Deployment complexity\n\n## Design Principles\n\n- Single responsibility\n- API-first design\n- Stateless services\n- Proper service boundaries\n\n## Communication Patterns\n\n- REST APIs\n- Message queues\n- Event-driven architecture",
                "category": "Web Development",
                "tags": ["REST API", "Best Practices", "Performance"]
            },
            {
                "title": "FastAPI Authentication and Authorization",
                "slug": "fastapi-authentication-authorization",
                "excerpt": "Implement secure authentication and authorization in FastAPI applications.",
                "content": "Security is crucial for APIs. This tutorial shows how to implement authentication in FastAPI.\n\n## JWT Authentication\n\n```python\nfrom jose import jwt\nfrom datetime import datetime, timedelta\n\nSECRET_KEY = \"your-secret-key\"\nALGORITHM = \"HS256\"\n\ndef create_access_token(data: dict):\n    to_encode = data.copy()\n    expire = datetime.utcnow() + timedelta(minutes=15)\n    to_encode.update({\"exp\": expire})\n    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)\n```\n\n## Dependency Injection\n\nUse FastAPI dependencies for authentication:\n```python\nfrom fastapi import Depends, HTTPException\n\ndef get_current_user(token: str = Depends(oauth2_scheme)):\n    # Verify token\n    return user\n```",
                "category": "Python",
                "tags": ["FastAPI", "REST API", "Best Practices"]
            },
            {
                "title": "MongoDB Indexing Strategies",
                "slug": "mongodb-indexing-strategies",
                "excerpt": "Optimize MongoDB queries with effective indexing strategies.",
                "content": "Proper indexing is crucial for MongoDB performance. This article covers indexing strategies.\n\n## Types of Indexes\n\n- Single field indexes\n- Compound indexes\n- Text indexes\n- Geospatial indexes\n\n## Index Creation\n\n```javascript\ndb.collection.createIndex({ field: 1 })\ndb.collection.createIndex({ field1: 1, field2: -1 })\n```\n\n## Best Practices\n\n- Index frequently queried fields\n- Consider query patterns\n- Monitor index usage\n- Avoid over-indexing\n\n## Index Analysis\n\nUse explain() to analyze query performance:\n```javascript\ndb.collection.find({ field: value }).explain(\"executionStats\")\n```",
                "category": "Database",
                "tags": ["MongoDB", "Database", "Performance"]
            },
            {
                "title": "React State Management: Redux vs Context API",
                "slug": "react-state-management-redux-vs-context-api",
                "excerpt": "Compare Redux and Context API for state management in React applications.",
                "content": "State management is crucial for React applications. This article compares Redux and Context API.\n\n## Context API\n\n### Pros\n- Built into React\n- Simple for small apps\n- No extra dependencies\n\n### Cons\n- Can cause re-renders\n- Not ideal for complex state\n\n## Redux\n\n### Pros\n- Predictable state updates\n- Great DevTools\n- Time-travel debugging\n\n### Cons\n- More boilerplate\n- Learning curve\n- Additional dependency\n\n## When to Use What?\n\n- Context API: Small to medium apps\n- Redux: Complex state, large teams",
                "category": "JavaScript",
                "tags": ["React", "JavaScript", "Best Practices"]
            },
            {
                "title": "Docker Compose for Multi-Container Applications",
                "slug": "docker-compose-multi-container-applications",
                "excerpt": "Learn how to orchestrate multiple containers with Docker Compose.",
                "content": "Docker Compose simplifies multi-container application management. This guide covers the essentials.\n\n## docker-compose.yml\n\n```yaml\nversion: '3.8'\nservices:\n  web:\n    build: .\n    ports:\n      - \"8000:8000\"\n  db:\n    image: postgres:13\n    environment:\n      POSTGRES_PASSWORD: password\n```\n\n## Common Commands\n\n```bash\ndocker-compose up\ndocker-compose down\ndocker-compose logs\ndocker-compose ps\n```\n\n## Networking\n\nServices can communicate using service names as hostnames.\n\n## Volumes\n\nPersist data with volumes:\n```yaml\nvolumes:\n  - ./data:/var/lib/postgresql/data\n```",
                "category": "DevOps",
                "tags": ["Docker", "DevOps", "Best Practices"]
            },
            {
                "title": "TypeScript Advanced Types and Patterns",
                "slug": "typescript-advanced-types-patterns",
                "excerpt": "Explore advanced TypeScript types and design patterns for better code quality.",
                "content": "TypeScript offers powerful type system features. This article covers advanced types.\n\n## Union Types\n\n```typescript\ntype Status = \"pending\" | \"approved\" | \"rejected\";\n```\n\n## Intersection Types\n\n```typescript\ntype User = Person & Account;\n```\n\n## Conditional Types\n\n```typescript\ntype NonNullable<T> = T extends null | undefined ? never : T;\n```\n\n## Mapped Types\n\n```typescript\ntype Readonly<T> = {\n  readonly [P in keyof T]: T[P];\n};\n```\n\n## Utility Types\n\n- Partial<T>\n- Required<T>\n- Pick<T, K>\n- Omit<T, K>",
                "category": "JavaScript",
                "tags": ["TypeScript", "JavaScript", "Best Practices"]
            },
            {
                "title": "AWS Lambda: Serverless Functions Guide",
                "slug": "aws-lambda-serverless-functions-guide",
                "excerpt": "Build and deploy serverless functions with AWS Lambda.",
                "content": "AWS Lambda lets you run code without managing servers. This guide covers Lambda basics.\n\n## What is Lambda?\n\nLambda is a serverless compute service that runs your code in response to events.\n\n## Creating a Lambda Function\n\n```python\nimport json\n\ndef lambda_handler(event, context):\n    return {\n        'statusCode': 200,\n        'body': json.dumps('Hello from Lambda!')\n    }\n```\n\n## Triggers\n\n- API Gateway\n- S3 events\n- DynamoDB streams\n- CloudWatch Events\n\n## Best Practices\n\n- Keep functions small\n- Use environment variables\n- Implement proper error handling\n- Monitor with CloudWatch",
                "category": "Cloud Computing",
                "tags": ["AWS", "Cloud Computing", "Best Practices"]
            },
            {
                "title": "API Rate Limiting Strategies",
                "slug": "api-rate-limiting-strategies",
                "excerpt": "Implement effective rate limiting to protect your APIs from abuse.",
                "content": "Rate limiting protects APIs from abuse and ensures fair resource usage. This article covers rate limiting strategies.\n\n## Why Rate Limiting?\n\n- Prevent abuse\n- Ensure fair usage\n- Protect resources\n- Improve reliability\n\n## Strategies\n\n### Fixed Window\nLimit requests per time window.\n\n### Sliding Window\nMore accurate but complex.\n\n### Token Bucket\nAllows bursts of traffic.\n\n## Implementation\n\nUse Redis for distributed rate limiting:\n```python\nimport redis\nr = redis.Redis()\n\nkey = f\"rate_limit:{user_id}\"\ncount = r.incr(key)\nif count == 1:\n    r.expire(key, 60)\n```\n\n## Best Practices\n\n- Set appropriate limits\n- Return clear error messages\n- Use HTTP 429 status code",
                "category": "Web Development",
                "tags": ["REST API", "Performance", "Best Practices"]
            }
        ]
        
        created_count = 0
        for post_data in posts_data:
            try:
                # Get category ID
                category_id = category_ids.get(post_data["category"])
                if not category_id:
                    print(f"Category '{post_data['category']}' not found, skipping post: {post_data['title']}")
                    continue
                
                # Get tag IDs
                tag_names = post_data.get("tags", [])
                tag_objects = [{"name": tag_name} for tag_name in tag_names]
                
                # Check if post already exists
                existing = await self.post_service.post_repo.collection.find_one({"slug": post_data["slug"], "deleted_at": None})
                if existing:
                    print(f"Post '{post_data['title']}' already exists, skipping...")
                    continue
                
                # Create post
                post = await self.post_service.create_post(
                    title=post_data["title"],
                    content=post_data["content"],
                    slug_str=post_data["slug"],
                    excerpt=post_data.get("excerpt"),
                    tags=tag_objects,
                    category_id=category_id,
                    user_id=user_id,
                    meta_title=post_data.get("meta_title"),
                    meta_description=post_data.get("meta_description")
                )
                
                # Publish the post
                if post and post.get("_id"):
                    await self.post_service.publish_post(str(post["_id"]))
                    created_count += 1
                    print(f"Created and published post: {post_data['title']}")
                
            except Exception as e:
                print(f"Error creating post '{post_data.get('title', 'Unknown')}': {e}")
        
        return created_count

    async def run(self):
        if settings.ENABLE_SEED_DATA:
            # Seed users first
            users = [
                {
                    "username": settings.DEFAULT_USER_FULL_NAME,
                    "email": settings.DEFAULT_USER_EMAIL,
                    "password": settings.DEFAULT_USER_PASSWORD,
                    "role": settings.DEFAULT_USER_ROLE,
                    "date_of_birth": settings.DEFAULT_USER_DATE_OF_BIRTH
                }
            ]   
            await self.seed_users(users)
            print("✓ Seed users completed")
            
            # Get user ID for posts
            user = await self.user_service.get_by_email(settings.DEFAULT_USER_EMAIL)
            if not user:
                print("Error: Default user not found. Cannot seed posts.")
                return
            
            user_id = str(user["_id"])
            
            # Seed categories
            print("\n=== Seeding Categories ===")
            category_ids = await self.seed_categories()
            print(f"✓ Created/verified {len(category_ids)} categories\n")
            
            # Seed tags
            print("=== Seeding Tags ===")
            tag_ids = await self.seed_tags()
            print(f"✓ Created/verified {len(tag_ids)} tags\n")
            
            # Seed posts
            print("=== Seeding Posts ===")
            created_posts = await self.seed_posts(user_id, category_ids, tag_ids)
            print(f"✓ Created and published {created_posts} posts\n")
            
            print("=== Seed Data Complete ===")

# run seed (use event startup)
async def seed_db():
    db = get_database()
    user_repo = MongoUserRepository(db)
    category_repo = MongoCategoryRepository(db)
    tag_repo = MongoTagRepository(db)
    post_repo = MongoPostRepository(db)
    user_repo_for_posts = MongoUserRepository(db)
    
    user_service = UserService(user_repo)
    category_service = CategoryService(category_repo)
    tag_service = TagService(tag_repo)
    post_service = PostService(post_repo, user_repo_for_posts, tag_repo)
    
    seeder = MongoSeeder(user_service, category_service, tag_service, post_service)
    await seeder.run()
