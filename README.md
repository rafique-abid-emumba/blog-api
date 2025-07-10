# Blog API

A robust, secure, and production-grade RESTful API for a blog platform, built with FastAPI and enhanced by Generative AI technologies.

---

## 🚀 Features

- **User Management**
  - Registration, login (JWT access & refresh tokens)
  - Profile view/update
  - Password hashing (bcrypt)
  - Role-Based Access Control (Admin, Author, Reader) via FastAPI dependencies

- **Post Management**
  - CRUD for blog posts (draft/published)
  - Tagging, filtering, search, pagination
  - Publishing workflow

- **Comment Management**
  - CRUD for comments
  - Nested comments (replies)
  - Pagination

- **Generative AI Integration**
  - Title & tag suggestions (Groq-hosted LLM, Cohere embeddings)
  - Summarization
  - Q&A (RAG with QDrant vector DB)
  - Comment sentiment analysis & abuse flagging
  - Trending tags
  - Citations/references in AI outputs

- **Security**
  - JWT authentication (access & refresh)
  - RBAC enforced via FastAPI dependencies (`require_role`)
  - Input validation

- **Testing & Quality**
  - Pytest for unit/integration tests
  - In-memory SQLite for fast, isolated test runs
  - Clean, idiomatic, DRY Python code (no comments in codebase)

- **Performance**
  - Redis caching

---

## 🛠️ Tech Stack

- **API Framework:** FastAPI
- **ORM:** SQLAlchemy
- **Database:** PostgreSQL
- **Authentication:** JWT (python-jose, bcrypt)
- **Vector DB:** QDrant
- **LLM:** Groq-hosted (e.g., LLaMA2/3)
- **Embeddings:** Cohere
- **GenAI Framework:** LlamaIndex or LangChain (to be decided)
- **Caching:** Redis
- **Testing:** Pytest
- **Dependency Management:** Poetry

---

## 📦 Setup Instructions

### 1. Clone the repository
```sh
git clone https://github.com/<your-username>/blog-api.git
cd blog-api
```

### 2. Install Poetry (if not already)
```sh
pip install poetry
# or
pipx install poetry
```

### 3. Install dependencies (including email-validator)
```sh
poetry add email-validator
poetry install
```

### 4. Set up environment variables

Create a `.env` file in the project root with your secrets:
```
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/blogdb
SECRET_KEY=your-secret-key
COHERE_API_KEY=your-cohere-key
GROQ_API_KEY=your-groq-key
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379/0
```
- All secrets are loaded and validated using Pydantic Settings.

### 5. Run database migrations
```sh
alembic upgrade head
```

### 6. Seed Initial Roles

Before registering users, you must seed the default roles into the database. This ensures the `role_id` foreign key constraint is satisfied when creating users.

Run the following command from your project root:
```sh
poetry run python -m app.db.seed_roles
```
This script will insert the default roles (`Admin`, `Author`, `Reader`) into the `roles` table if they do not already exist.

Alternatively, you can run this SQL command in your PostgreSQL client:
```sql
INSERT INTO roles (name) VALUES ('Admin'), ('Author'), ('Reader');
```
**You must perform this step after running your first Alembic migration and before registering any users.**

### 7. Start the development server
```sh
poetry run uvicorn app.main:app --reload
```

### 8. Access API docs
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Testing

- All tests use **in-memory SQLite** for speed and isolation.=
- To run all tests:
```sh
poetry run python -m pytest -v app/tests/
```

## Running Tests with Coverage

To run tests and measure code coverage:

```bash
pytest --cov=app --cov-report=term-missing app/tests
```

To generate an HTML coverage report:

```bash
pytest --cov=app --cov-report=html app/tests
# Open the report in your browser:
# On Windows:
start htmlcov/index.html
# On macOS:
open htmlcov/index.html
# On Linux:
x-www-browser htmlcov/index.html
```

Make sure you have `pytest-cov` installed:

```bash
poetry add --dev pytest-cov
```

---

## 📝 Documentation

- API documentation is auto-generated at `/docs` (Swagger UI).
- For architecture, design decisions, and GenAI integration, see the `docs/` folder (to be created).

---

## 🔐 Role-Based Access Control (RBAC)

RBAC is enforced using FastAPI dependencies (`require_role`).

| Role   | Can Create Posts | Can Edit Own Posts | Can Edit Any Post | Can Delete Own Posts | Can Delete Any Post | Can View Drafts | Can Manage Users |
|--------|:----------------:|:------------------:|:-----------------:|:-------------------:|:-------------------:|:---------------:|:----------------:|
| Admin  |        ✅        |        ✅          |        ✅         |        ✅           |        ✅           |       ✅        |       ✅         |
| Author |        ✅        |        ✅          |        ❌         |        ✅           |        ❌           | Own only        |       ❌         |
| Reader |        ❌        |        ❌          |        ❌         |        ❌           |        ❌           | Published only  |       ❌         |

---

## 🧩 Architecture & Code Quality

- **Clean architecture:** API layer (routing), service layer (business logic), models, schemas, etc.
- **Error handling:** Consistent use of custom exceptions and HTTP status codes in the service layer.
- **Validation:** Input validation for registration, post creation, etc.
- **No comments:** Codebase is clean and self-explanatory, following DRY and idiomatic Python best practices.

---

## 🤝 Contributing

1. Fork the repo and create your branch (`git checkout -b feature/your-feature`)
2. Commit your changes (`git commit -am 'Add new feature'`)
3. Push to the branch (`git push origin feature/your-feature`)
4. Create a new Pull Request

---

## 📄 License

[MIT License](LICENSE) (or specify your preferred license)

---

## 🌟 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [QDrant](https://qdrant.tech/)
- [Cohere](https://cohere.com/)
- [Groq](https://groq.com/)
- [LlamaIndex](https://llamaindex.ai/)
- [LangChain](https://www.langchain.com/)

---

> **Note:** This project is under active development. Features and documentation will evolve as the project progresses. 

---

## 🔑 Authentication, Token Rotation, and Revocation

- **JWT access and refresh tokens** are used for authentication.
- **Refresh token rotation** is implemented: every time a refresh token is used, a new one is issued and the old one is blacklisted.
- **Token revocation/blacklisting** is handled using Redis. If a refresh token is used again after rotation, it is rejected.
- **Redis setup:**
  - For development, run Redis with Docker:
    ```sh
    docker run -d --name blog-redis -p 6379:6379 redis
    ```
  - Set `REDIS_URL=redis://localhost:6379/0` in your `.env` file.
  - In production, use a managed Redis service (AWS ElastiCache, Azure, Redis Cloud, etc.).
- **All token logic is modularized in `auth_service.py` for clean architecture.**

---
