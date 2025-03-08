/flask_bi_ai
│── /app
│   ├── /api
│   │   ├── __init__.py
│   │   ├── auth.py                # JWT auth, RBAC implementation
│   │   ├── documents.py           # Document management (upload, processing)
│   │   ├── insights.py            # LLM-based business insights & risk detection
│   │   ├── search.py              # RAG-based document search with filtering
│   │   ├── users.py               # User management with role definitions
│   │   ├── urls.py                # URL analysis & information extraction
│   │   ├── dashboard.py           # Visualization & reporting endpoints
│   │   ├── audit.py               # Audit logging for compliance
│   │   
│   ├── /models
│   │   ├── __init__.py
│   │   ├── user.py                # User model with RBAC
│   │   ├── document.py            # Document metadata & storage references
│   │   ├── chat_history.py        # Query history for auditing & improvement
│   │   ├── vector_store.py        # Vector DB schema & interfaces
│   │   ├── audit_log.py           # Comprehensive logging for compliance
│   │   
│   ├── /services
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── llm_manager.py     # Model selection (DeepSeek, Mistral, Llama3)
│   │   │   ├── document_qa.py     # Document question-answering
│   │   │   ├── risk_analyzer.py   # Financial & operational risk detection
│   │   │   ├── forecasting.py     # Trend prediction & anomaly detection
│   │   │   ├── prompt_templates.py # Optimized prompts for each use case
│   │   │
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── vector_db.py       # ChromaDB/Weaviate operations
│   │   │   ├── document_processor.py # Multi-format document handling
│   │   │   ├── ocr_service.py     # OCR for scanned documents
│   │   │   ├── table_extractor.py # Extract & analyze tabular data
│   │   │   ├── url_scraper.py     # URL content extraction & processing
│   │   │   ├── etl_pipeline.py    # Data transformation pipelines
│   │   │
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── jwt_handler.py     # JWT token management
│   │   │   ├── rbac.py            # Role-based access control
│   │   │   ├── oauth_provider.py  # OAuth2 integration
│   │   │
│   │   ├── async_tasks/
│   │   │   ├── __init__.py
│   │   │   ├── celery_config.py   # Celery configuration
│   │   │   ├── document_tasks.py  # Async document processing
│   │   │   ├── insight_tasks.py   # Background AI analysis
│   │
│── /templates
│   ├── base.html                  # Base template with navigation
│   ├── dashboard/
│   │   ├── main.html              # AI insights dashboard
│   │   ├── reports.html           # Generated reports view
│   │   ├── document_viewer.html   # Interactive document viewer
│   │   ├── visualization.html     # Charts & data visualization
│   ├── admin/
│   │   ├── user_management.html   # User & role management
│   │   ├── system_settings.html   # Platform configuration
│   │   ├── audit_logs.html        # Compliance monitoring
│   ├── auth/
│   │   ├── login.html             # Authentication
│   │   ├── register.html          # New user registration
│   │   ├── profile.html           # User profile management
│
│── /static
│   ├── /css
│   │   ├── tailwind.css           # Tailwind CSS framework
│   │   ├── custom.css             # Custom styling
│   ├── /js
│   │   ├── chart.js              # Chart.js/Plotly integration
│   │   ├── document_viewer.js    # Document interaction
│   │   ├── dashboard.js          # Dashboard interactivity
│   │   ├── query_builder.js      # Natural language query builder
│
│── /config
│   ├── base.py                    # Shared configuration
│   ├── production.py              # Production settings
│   ├── development.py             # Development settings
│   ├── testing.py                 # Test environment settings
│
│── /tests
│   ├── /unit
│   │   ├── test_auth.py           # Authentication tests
│   │   ├── test_document_processing.py # Document handling tests
│   │   ├── test_ai_services.py    # AI service tests
│   ├── /integration
│   │   ├── test_api.py            # API integration tests
│   │   ├── test_end_to_end.py     # Complete workflow tests
│
│── /migrations                     # Database migrations (Alembic)
│
│── /scripts
│   ├── setup_db.py                 # Database initialization
│   ├── import_demo_data.py         # Sample data for testing
│   ├── generate_keys.py            # Security key generation
│
│── main.py                         # Application entry point
│── wsgi.py                         # WSGI server entry
│── celery_worker.py                # Celery worker configuration
│── requirements.txt                # Dependencies
│── .env.example                    # Environment variable template
│── .gitignore                      # Git ignore patterns
│── Dockerfile                      # Container configuration
│── docker-compose.yml              # Multi-container setup
│── docker-compose.prod.yml         # Production deployment
│── nginx.conf                      # Nginx configuration for production
│── README.md                       # Project documentation




flask db init
flask db migrate -m "Initial migration"
flask db upgrade



admin
admin@123


usertapan
usertapan@gmail.com