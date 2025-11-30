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
                "content": "<p>FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints. In this comprehensive guide, we'll explore how to get started with FastAPI, set up your first project, and build a RESTful API.</p><h2>Installation</h2><p>First, install FastAPI and Uvicorn:</p><pre class=\"language-bash\"><code>pip install fastapi uvicorn</code></pre><h2>Creating Your First API</h2><p>Let's create a simple API endpoint:</p><pre class=\"language-python\"><code>from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get(\"/\")\ndef read_root():\n    return {\"Hello\": \"World\"}</code></pre><h2>Running the Server</h2><p>Start your server with:</p><pre class=\"language-bash\"><code>uvicorn main:app --reload</code></pre><p>FastAPI automatically generates interactive API documentation at <code>/docs</code> and <code>/redoc</code>.</p>",
                "category": "Python",
                "tags": ["FastAPI", "REST API"],
                "meta_title": "Getting Started with FastAPI - Complete Guide",
                "meta_description": "Learn how to build modern APIs with FastAPI. Complete tutorial with examples and best practices."
            },
            {
                "title": "Building RESTful APIs: Best Practices",
                "slug": "building-restful-apis-best-practices",
                "excerpt": "Discover the essential best practices for designing and implementing RESTful APIs that are scalable and maintainable.",
                "content": "<p>RESTful APIs are the backbone of modern web applications. In this article, we'll explore best practices for designing and implementing RESTful APIs that are scalable, maintainable, and developer-friendly.</p><h2>Use Proper HTTP Methods</h2><ul><li><strong>GET:</strong> Retrieve resources</li><li><strong>POST:</strong> Create new resources</li><li><strong>PUT:</strong> Update entire resources</li><li><strong>PATCH:</strong> Partial updates</li><li><strong>DELETE:</strong> Remove resources</li></ul><h2>Consistent Naming Conventions</h2><p>Use plural nouns for resource names:</p><ul><li><code>/api/users</code> (not <code>/api/user</code>)</li><li><code>/api/posts</code> (not <code>/api/post</code>)</li></ul><h2>Versioning</h2><p>Always version your APIs:</p><ul><li><code>/api/v1/users</code></li><li><code>/api/v2/users</code></li></ul><h2>Error Handling</h2><p>Return appropriate HTTP status codes and consistent error formats.</p>",
                "category": "Web Development",
                "tags": ["REST API", "Best Practices"],
                "meta_title": "RESTful API Best Practices Guide"
            },
            {
                "title": "React Hooks: A Complete Guide",
                "slug": "react-hooks-complete-guide",
                "excerpt": "Master React Hooks with this comprehensive guide covering useState, useEffect, and custom hooks.",
                "content": "<p>React Hooks revolutionized how we write React components. Introduced in React 16.8, hooks allow you to use state and other React features without writing a class.</p><h2>useState Hook</h2><p>The useState hook lets you add state to functional components:</p><pre class=\"language-javascript\"><code>import { useState } from 'react';\n\nfunction Counter() {\n  const [count, setCount] = useState(0);\n  return (\n    &lt;div&gt;\n      &lt;p&gt;You clicked {count} times&lt;/p&gt;\n      &lt;button onClick={() =&gt; setCount(count + 1)}&gt;Click me&lt;/button&gt;\n    &lt;/div&gt;\n  );\n}</code></pre><h2>useEffect Hook</h2><p>useEffect lets you perform side effects in functional components:</p><pre class=\"language-javascript\"><code>useEffect(() =&gt; {\n  document.title = `You clicked ${count} times`;\n}, [count]);</code></pre><h2>Custom Hooks</h2><p>You can create custom hooks to share stateful logic between components.</p>",
                "category": "JavaScript",
                "tags": ["React", "JavaScript", "Best Practices"]
            },
            {
                "title": "Docker Containerization: From Basics to Production",
                "slug": "docker-containerization-basics-production",
                "excerpt": "Learn Docker from the ground up and deploy containerized applications to production.",
                "content": "<p>Docker has become the standard for containerization in modern software development. This guide will take you from Docker basics to production deployment.</p><h2>What is Docker?</h2><p>Docker is a platform for developing, shipping, and running applications in containers. Containers package an application with all its dependencies.</p><h2>Basic Docker Commands</h2><pre class=\"language-bash\"><code># Build an image\ndocker build -t myapp .\n\n# Run a container\ndocker run -p 3000:3000 myapp\n\n# List containers\ndocker ps\n\n# View logs\ndocker logs &lt;container_id&gt;</code></pre><h2>Dockerfile Best Practices</h2><ul><li>Use multi-stage builds</li><li>Minimize layers</li><li>Use .dockerignore</li><li>Don't run as root</li></ul><h2>Docker Compose</h2><p>Docker Compose allows you to define and run multi-container applications.</p>",
                "category": "DevOps",
                "tags": ["Docker", "DevOps", "Best Practices"]
            },
            {
                "title": "MongoDB Aggregation Pipeline Explained",
                "slug": "mongodb-aggregation-pipeline-explained",
                "excerpt": "Master MongoDB's powerful aggregation framework with practical examples and use cases.",
                "content": "<p>MongoDB's aggregation pipeline is a powerful framework for data processing. It allows you to transform and combine documents from a collection.</p><h2>Pipeline Stages</h2><p>The aggregation pipeline consists of stages:</p><ul><li><code>$match</code>: Filter documents</li><li><code>$group</code>: Group documents</li><li><code>$sort</code>: Sort documents</li><li><code>$project</code>: Reshape documents</li><li><code>$lookup</code>: Join collections</li></ul><h2>Example</h2><pre class=\"language-javascript\"><code>db.orders.aggregate([\n  { $match: { status: \"completed\" } },\n  { $group: { _id: \"$customer\", total: { $sum: \"$amount\" } } },\n  { $sort: { total: -1 } }\n])</code></pre><h2>Performance Tips</h2><ul><li>Use indexes</li><li>Filter early with <code>$match</code></li><li>Limit results</li><li>Use <code>$project</code> to reduce data</li></ul>",
                "category": "Database",
                "tags": ["MongoDB", "Database", "Best Practices"]
            },
            {
                "title": "TypeScript: Type Safety in JavaScript",
                "slug": "typescript-type-safety-javascript",
                "excerpt": "Discover how TypeScript brings type safety to JavaScript development.",
                "content": "<p>TypeScript is a typed superset of JavaScript that compiles to plain JavaScript. It adds static type definitions to JavaScript.</p><h2>Why TypeScript?</h2><ul><li>Catch errors early</li><li>Better IDE support</li><li>Improved code documentation</li><li>Easier refactoring</li></ul><h2>Basic Types</h2><pre class=\"language-typescript\"><code>let name: string = \"John\";\nlet age: number = 30;\nlet isActive: boolean = true;\nlet items: string[] = [\"apple\", \"banana\"];</code></pre><h2>Interfaces</h2><pre class=\"language-typescript\"><code>interface User {\n  id: number;\n  name: string;\n  email?: string;\n}\n\nconst user: User = {\n  id: 1,\n  name: \"John\"\n};</code></pre><h2>Generics</h2><p>TypeScript generics allow you to create reusable components.</p>",
                "category": "JavaScript",
                "tags": ["TypeScript", "JavaScript", "Best Practices"]
            },
            {
                "title": "AWS Cloud Services Overview",
                "slug": "aws-cloud-services-overview",
                "excerpt": "An introduction to Amazon Web Services and its key services for developers.",
                "content": "<p>Amazon Web Services (AWS) is a comprehensive cloud computing platform offering over 200 services. This article provides an overview of key AWS services.</p><h2>Core Services</h2><h3>EC2 (Elastic Compute Cloud)</h3><p>Virtual servers in the cloud.</p><h3>S3 (Simple Storage Service)</h3><p>Object storage for files and data.</p><h3>RDS (Relational Database Service)</h3><p>Managed database service.</p><h3>Lambda</h3><p>Serverless compute service.</p><h2>Getting Started</h2><ol><li>Create an AWS account</li><li>Set up IAM users</li><li>Configure AWS CLI</li><li>Deploy your first service</li></ol><h2>Best Practices</h2><ul><li>Use IAM roles</li><li>Enable CloudTrail</li><li>Set up billing alerts</li><li>Use multiple availability zones</li></ul>",
                "category": "Cloud Computing",
                "tags": ["AWS", "Cloud Computing", "Best Practices"]
            },
            {
                "title": "Testing Strategies for Modern Applications",
                "slug": "testing-strategies-modern-applications",
                "excerpt": "Learn effective testing strategies including unit, integration, and end-to-end testing.",
                "content": "<p>Testing is crucial for maintaining code quality and preventing bugs. This guide covers different testing strategies.</p><h2>Types of Tests</h2><h3>Unit Tests</h3><p>Test individual components in isolation.</p><h3>Integration Tests</h3><p>Test how components work together.</p><h3>E2E Tests</h3><p>Test the entire application flow.</p><h2>Testing Pyramid</h2><ul><li>Many unit tests (base)</li><li>Some integration tests (middle)</li><li>Few E2E tests (top)</li></ul><h2>Tools</h2><ul><li>Jest for JavaScript</li><li>Pytest for Python</li><li>Cypress for E2E</li></ul><h2>Best Practices</h2><ul><li>Write tests first (TDD)</li><li>Keep tests independent</li><li>Use mocks sparingly</li><li>Test edge cases</li></ul>",
                "category": "Tutorials",
                "tags": ["Testing", "Best Practices", "Performance"]
            },
            {
                "title": "Performance Optimization Techniques",
                "slug": "performance-optimization-techniques",
                "excerpt": "Essential techniques to improve application performance and user experience.",
                "content": "<p>Performance optimization is critical for user experience. This article covers key optimization techniques.</p><h2>Frontend Optimization</h2><ul><li>Code splitting</li><li>Lazy loading</li><li>Image optimization</li><li>Caching strategies</li></ul><h2>Backend Optimization</h2><ul><li>Database indexing</li><li>Query optimization</li><li>Caching layers</li><li>Connection pooling</li></ul><h2>Monitoring</h2><ul><li>Use APM tools</li><li>Monitor key metrics</li><li>Set up alerts</li><li>Regular profiling</li></ul><h2>Tools</h2><ul><li>Lighthouse for web performance</li><li>New Relic for APM</li><li>Redis for caching</li></ul>",
                "category": "Web Development",
                "tags": ["Performance", "Best Practices"]
            },
            {
                "title": "Security Best Practices for Web Applications",
                "slug": "security-best-practices-web-applications",
                "excerpt": "Essential security practices to protect your web applications from common vulnerabilities.",
                "content": "<p>Security is paramount in web development. This guide covers essential security practices.</p><h2>Common Vulnerabilities</h2><ul><li>SQL Injection</li><li>XSS (Cross-Site Scripting)</li><li>CSRF (Cross-Site Request Forgery)</li><li>Authentication flaws</li></ul><h2>Best Practices</h2><h3>Input Validation</h3><p>Always validate and sanitize user input.</p><h3>Authentication</h3><ul><li>Use strong passwords</li><li>Implement 2FA</li><li>Secure session management</li></ul><h3>HTTPS</h3><p>Always use HTTPS in production.</p><h3>Dependency Management</h3><p>Keep dependencies updated and scan for vulnerabilities.</p><h2>Tools</h2><ul><li>OWASP ZAP for security testing</li><li>Snyk for dependency scanning</li><li>Helmet.js for Express security</li></ul>",
                "category": "Security",
                "tags": ["Best Practices"]
            },
            {
                "title": "Introduction to Machine Learning",
                "slug": "introduction-machine-learning",
                "excerpt": "A beginner-friendly introduction to machine learning concepts and applications.",
                "content": "<p>Machine Learning is transforming industries. This article provides an introduction to ML concepts.</p><h2>What is Machine Learning?</h2><p>Machine Learning enables computers to learn from data without explicit programming.</p><h2>Types of Learning</h2><h3>Supervised Learning</h3><p>Learning with labeled data.</p><h3>Unsupervised Learning</h3><p>Finding patterns in unlabeled data.</p><h3>Reinforcement Learning</h3><p>Learning through interaction and rewards.</p><h2>Common Algorithms</h2><ul><li>Linear Regression</li><li>Decision Trees</li><li>Neural Networks</li><li>K-Means Clustering</li></ul><h2>Getting Started</h2><ul><li>Learn Python</li><li>Study mathematics (linear algebra, statistics)</li><li>Practice with datasets</li><li>Use libraries like scikit-learn</li></ul>",
                "category": "Machine Learning",
                "tags": ["Best Practices"]
            },
            {
                "title": "Mobile App Development: React Native vs Flutter",
                "slug": "mobile-app-development-react-native-vs-flutter",
                "excerpt": "Compare React Native and Flutter to choose the right framework for your mobile app project.",
                "content": "<p>Choosing between React Native and Flutter is a common dilemma. This article compares both frameworks.</p><h2>React Native</h2><h3>Pros</h3><ul><li>Large community</li><li>JavaScript/TypeScript</li><li>Hot reload</li><li>Native performance</li></ul><h3>Cons</h3><ul><li>Platform-specific code needed</li><li>Larger app size</li></ul><h2>Flutter</h2><h3>Pros</h3><ul><li>Single codebase</li><li>Fast performance</li><li>Beautiful UI</li><li>Strong typing (Dart)</li></ul><h3>Cons</h3><ul><li>Smaller community</li><li>Newer ecosystem</li></ul><h2>When to Choose What?</h2><ul><li><strong>React Native:</strong> If you know JavaScript</li><li><strong>Flutter:</strong> If you want consistent UI across platforms</li></ul>",
                "category": "Mobile Development",
                "tags": ["React", "Mobile Development", "Best Practices"]
            },
            {
                "title": "Building Scalable Microservices Architecture",
                "slug": "building-scalable-microservices-architecture",
                "excerpt": "Learn how to design and implement scalable microservices architectures.",
                "content": "<p>Microservices architecture breaks applications into small, independent services. This guide covers best practices.</p><h2>Benefits</h2><ul><li>Independent deployment</li><li>Technology diversity</li><li>Scalability</li><li>Fault isolation</li></ul><h2>Challenges</h2><ul><li>Service communication</li><li>Data consistency</li><li>Distributed tracing</li><li>Deployment complexity</li></ul><h2>Design Principles</h2><ul><li>Single responsibility</li><li>API-first design</li><li>Stateless services</li><li>Proper service boundaries</li></ul><h2>Communication Patterns</h2><ul><li>REST APIs</li><li>Message queues</li><li>Event-driven architecture</li></ul>",
                "category": "Web Development",
                "tags": ["REST API", "Best Practices", "Performance"]
            },
            {
                "title": "FastAPI Authentication and Authorization",
                "slug": "fastapi-authentication-authorization",
                "excerpt": "Implement secure authentication and authorization in FastAPI applications.",
                "content": "<p>Security is crucial for APIs. This tutorial shows how to implement authentication in FastAPI.</p><h2>JWT Authentication</h2><pre class=\"language-python\"><code>from jose import jwt\nfrom datetime import datetime, timedelta\n\nSECRET_KEY = \"your-secret-key\"\nALGORITHM = \"HS256\"\n\ndef create_access_token(data: dict):\n    to_encode = data.copy()\n    expire = datetime.utcnow() + timedelta(minutes=15)\n    to_encode.update({\"exp\": expire})\n    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)</code></pre><h2>Dependency Injection</h2><p>Use FastAPI dependencies for authentication:</p><pre class=\"language-python\"><code>from fastapi import Depends, HTTPException\n\ndef get_current_user(token: str = Depends(oauth2_scheme)):\n    # Verify token\n    return user</code></pre>",
                "category": "Python",
                "tags": ["FastAPI", "REST API", "Best Practices"]
            },
            {
                "title": "MongoDB Indexing Strategies",
                "slug": "mongodb-indexing-strategies",
                "excerpt": "Optimize MongoDB queries with effective indexing strategies.",
                "content": "<p>Proper indexing is crucial for MongoDB performance. This article covers indexing strategies.</p><h2>Types of Indexes</h2><ul><li>Single field indexes</li><li>Compound indexes</li><li>Text indexes</li><li>Geospatial indexes</li></ul><h2>Index Creation</h2><pre class=\"language-javascript\"><code>db.collection.createIndex({ field: 1 })\ndb.collection.createIndex({ field1: 1, field2: -1 })</code></pre><h2>Best Practices</h2><ul><li>Index frequently queried fields</li><li>Consider query patterns</li><li>Monitor index usage</li><li>Avoid over-indexing</li></ul><h2>Index Analysis</h2><p>Use explain() to analyze query performance:</p><pre class=\"language-javascript\"><code>db.collection.find({ field: value }).explain(\"executionStats\")</code></pre>",
                "category": "Database",
                "tags": ["MongoDB", "Database", "Performance"]
            },
            {
                "title": "React State Management: Redux vs Context API",
                "slug": "react-state-management-redux-vs-context-api",
                "excerpt": "Compare Redux and Context API for state management in React applications.",
                "content": "<p>State management is crucial for React applications. This article compares Redux and Context API.</p><h2>Context API</h2><h3>Pros</h3><ul><li>Built into React</li><li>Simple for small apps</li><li>No extra dependencies</li></ul><h3>Cons</h3><ul><li>Can cause re-renders</li><li>Not ideal for complex state</li></ul><h2>Redux</h2><h3>Pros</h3><ul><li>Predictable state updates</li><li>Great DevTools</li><li>Time-travel debugging</li></ul><h3>Cons</h3><ul><li>More boilerplate</li><li>Learning curve</li><li>Additional dependency</li></ul><h2>When to Use What?</h2><ul><li><strong>Context API:</strong> Small to medium apps</li><li><strong>Redux:</strong> Complex state, large teams</li></ul>",
                "category": "JavaScript",
                "tags": ["React", "JavaScript", "Best Practices"]
            },
            {
                "title": "Docker Compose for Multi-Container Applications",
                "slug": "docker-compose-multi-container-applications",
                "excerpt": "Learn how to orchestrate multiple containers with Docker Compose.",
                "content": "<p>Docker Compose simplifies multi-container application management. This guide covers the essentials.</p><h2>docker-compose.yml</h2><pre class=\"language-yaml\"><code>version: '3.8'\nservices:\n  web:\n    build: .\n    ports:\n      - \"8000:8000\"\n  db:\n    image: postgres:13\n    environment:\n      POSTGRES_PASSWORD: password</code></pre><h2>Common Commands</h2><pre class=\"language-bash\"><code>docker-compose up\ndocker-compose down\ndocker-compose logs\ndocker-compose ps</code></pre><h2>Networking</h2><p>Services can communicate using service names as hostnames.</p><h2>Volumes</h2><p>Persist data with volumes:</p><pre class=\"language-yaml\"><code>volumes:\n  - ./data:/var/lib/postgresql/data</code></pre>",
                "category": "DevOps",
                "tags": ["Docker", "DevOps", "Best Practices"]
            },
            {
                "title": "TypeScript Advanced Types and Patterns",
                "slug": "typescript-advanced-types-patterns",
                "excerpt": "Explore advanced TypeScript types and design patterns for better code quality.",
                "content": "<p>TypeScript offers powerful type system features. This article covers advanced types.</p><h2>Union Types</h2><pre class=\"language-typescript\"><code>type Status = \"pending\" | \"approved\" | \"rejected\";</code></pre><h2>Intersection Types</h2><pre class=\"language-typescript\"><code>type User = Person & Account;</code></pre><h2>Conditional Types</h2><pre class=\"language-typescript\"><code>type NonNullable&lt;T&gt; = T extends null | undefined ? never : T;</code></pre><h2>Mapped Types</h2><pre class=\"language-typescript\"><code>type Readonly&lt;T&gt; = {\n  readonly [P in keyof T]: T[P];\n};</code></pre><h2>Utility Types</h2><ul><li><code>Partial&lt;T&gt;</code></li><li><code>Required&lt;T&gt;</code></li><li><code>Pick&lt;T, K&gt;</code></li><li><code>Omit&lt;T, K&gt;</code></li></ul>",
                "category": "JavaScript",
                "tags": ["TypeScript", "JavaScript", "Best Practices"]
            },
            {
                "title": "AWS Lambda: Serverless Functions Guide",
                "slug": "aws-lambda-serverless-functions-guide",
                "excerpt": "Build and deploy serverless functions with AWS Lambda.",
                "content": "<p>AWS Lambda lets you run code without managing servers. This guide covers Lambda basics.</p><h2>What is Lambda?</h2><p>Lambda is a serverless compute service that runs your code in response to events.</p><h2>Creating a Lambda Function</h2><pre class=\"language-python\"><code>import json\n\ndef lambda_handler(event, context):\n    return {\n        'statusCode': 200,\n        'body': json.dumps('Hello from Lambda!')\n    }</code></pre><h2>Triggers</h2><ul><li>API Gateway</li><li>S3 events</li><li>DynamoDB streams</li><li>CloudWatch Events</li></ul><h2>Best Practices</h2><ul><li>Keep functions small</li><li>Use environment variables</li><li>Implement proper error handling</li><li>Monitor with CloudWatch</li></ul>",
                "category": "Cloud Computing",
                "tags": ["AWS", "Cloud Computing", "Best Practices"]
            },
            {
                "title": "API Rate Limiting Strategies",
                "slug": "api-rate-limiting-strategies",
                "excerpt": "Implement effective rate limiting to protect your APIs from abuse.",
                "content": "<p>Rate limiting protects APIs from abuse and ensures fair resource usage. This article covers rate limiting strategies.</p><h2>Why Rate Limiting?</h2><ul><li>Prevent abuse</li><li>Ensure fair usage</li><li>Protect resources</li><li>Improve reliability</li></ul><h2>Strategies</h2><h3>Fixed Window</h3><p>Limit requests per time window.</p><h3>Sliding Window</h3><p>More accurate but complex.</p><h3>Token Bucket</h3><p>Allows bursts of traffic.</p><h2>Implementation</h2><p>Use Redis for distributed rate limiting:</p><pre class=\"language-python\"><code>import redis\nr = redis.Redis()\n\nkey = f\"rate_limit:{user_id}\"\ncount = r.incr(key)\nif count == 1:\n    r.expire(key, 60)</code></pre><h2>Best Practices</h2><ul><li>Set appropriate limits</li><li>Return clear error messages</li><li>Use HTTP 429 status code</li></ul>"
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
                if post and post.id:
                    await self.post_service.publish_post(str(post.id))
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
