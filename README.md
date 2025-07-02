# Blog API

A robust, secure, and production-grade RESTful API for a blog platform, built with FastAPI and enhanced by Generative AI technologies.

---

## 🚀 Features

- **User Management**
  - Registration, login (JWT access & refresh tokens)
  - Profile view/update
  - Password hashing (bcrypt)
  - Role-Based Access Control (Admin, Author, Reader)

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
  - RBAC middleware
  - Input validation

- **Testing & Quality**
  - Pytest for unit/integration tests

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

Run all tests with:
```sh
poetry run pytest
```

---

## 📝 Documentation

- API documentation is auto-generated at `/docs` (Swagger UI).
- For architecture, design decisions, and GenAI integration, see the `docs/` folder (to be created).

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