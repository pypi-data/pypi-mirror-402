# Recurve Libraries

For the unified maintenance of public components of the Recurve platform,
these codes may be used in both Server and Executor (Worker) environments.

Only Python 3.11+ are supported.

## Components

This code repository consists of the following core components:

### Core
The foundation of the Recurve platform that provides:

- Base classes and interfaces for platform components
- Jinja2 templating engine integration
- Core configuration management
- Common platform abstractions

### Utils
A comprehensive utility library offering:

- Time handling and date manipulation
- Concurrent processing tools
- File system operations and path handling
- String manipulation and text processing
- Logging and error handling utilities
- Data validation helpers

### Connectors
A robust data connectivity layer supporting:
- Database connections (MySQL, PostgreSQL, Redshift, BigQuery, etc.)
- Cloud storage (S3, GCS, Azure Blob Storage)
- Messaging services and APIs
- Custom connector development framework

Note: Run `make update-connector-schema` after updating connector config schemas to regenerate config_schema.py

### Schedulers
Airflow integration components including:

- Custom Airflow operators and sensors
- DAG generation utilities
- Workflow scheduling interfaces
- Task dependency management

### Operators
Task-specific operators for:

- Data extraction and loading
- Data transformation and processing
- Running Python code
- Running SQL code
- Building and running DBT jobs


### Client
A flexible client interface providing:

- Platform API abstractions
- Authentication handling
- Resource management
- Extensible base classes for custom clients
- Connection pooling and retry logic

### Executors

Core job execution engine that:

- Manages job submissions and execution flows
- Orchestrates task execution on infrastructure
- Handles job lifecycle and state management
- Provides infrastructure abstraction layer

## Development Workflow

### Requirements management

We use `uv` to manage Python package dependencies. The workflow is:

1. Update source requirements in `.in` files:
   - [`requirements.in`](./requirements.in) - All dependencies
   - [`requirements/worker.in`](requirements/worker.in) - Worker-specific dependencies
   - [`requirements/dbt.in`](requirements/dbt.in) - DBT-specific dependencies
   - [`requirements-dev.in`](requirements-dev.in) - Development dependencies

2. Compile locked requirements:
   ```bash
   make compile-requirements  # Compiles all requirements files
   ```
   Or compile individual files:
   ```bash
   make compile-worker  # Just worker requirements
   make compile-dbt    # Just DBT requirements
   ```

3. After compiling requirements, update optional dependencies in pyproject.toml:
   ```bash
   make update-optional-deps
   ```

This ensures consistent dependencies across development and production environments.

### Release Process

1. Update version number in [`recurvedata/__version__.py`](recurvedata/__version__.py)
2. Build and publish package:
   ```bash
   make publish
   ```
   This will clean build artifacts, build new package, and publish to Recurve PyPI.

### Available Commands

The following make commands are available:

Build and Publishing:
- `make clean` - Remove build artifacts (dist directory)
- `make build` - Clean and build the package
- `make publish` - Build and publish package to Recurve PyPI

Requirements Management:
- `make upgrade-uv` - Upgrade the uv package installer
- `make compile-worker` - Compile worker-specific requirements
- `make compile-dbt` - Compile DBT-specific requirements
- `make compile-requirements` - Compile all requirements files and sync environment
- `make install-requirements` - Install requirements files

Maintenance Scripts:
- `make update-optional-deps` - Update optional dependencies in pyproject.toml
- `make update-connector-schema` - Update connector configuration schemas

## GitLab CI/CD Pipeline

### Overview
This repository uses GitLab CI for build and release. The primary stages (in order) are:
- python_internal: build and publish internal PyPI package (develop)
- python_public: build and publish public PyPI package (main, manual)
- copy_dockerfiles: prepare Docker build context and version metadata
- docker_internal: build and push internal Docker images (develop / release/*)
- docker_official: build and push public Docker images (main, manual)
- scan: SAST/Sonar (disabled by default)

Configuration files:
- `.gitlab-ci.yml` (stages, rules, job orchestration)
- `.gitlab/ci/templates.yml` (shared templates and login configuration)
- `.gitlab/ci/variables.yml` (shared variables)
- `dockerfiles/build_push_images.sh` (image build and push script)

### Branch rules and triggers
- develop branch
  - Runs: `check_version` → `package_python_internal` → `copy_dockerfiles` → `build_docker_internal`
  - Environment: `ENVIRONMENT=test`
  - Targets: internal private registry + Aliyun `internal` namespace

- release/* branches
  - Runs: `copy_dockerfiles` → `build_docker_internal`
  - Environment: `ENVIRONMENT=staging`
  - Targets: internal private registry + Aliyun `internal` namespace

- main branch
  - Runs (manual): `package_python_public`, `build_docker_public`, `tag`
  - Environment: `ENVIRONMENT=production`
  - Targets: Docker Hub public registry + Aliyun `public` namespace

Note: the `tag` job creates an annotated tag after the public image build, including deployment metadata.

### Image build and naming
Build script: `dockerfiles/build_push_images.sh`
- Image names:
  - Production: `recurve-<service>` (current service = worker)
  - Non-production: `recurve-<service>-<environment>` (e.g., `recurve-worker-test`, `recurve-worker-staging`)
- Tags:
  - version: `${VERSION_PACKAGE}` (from `recurvedata/__version__.py`)
  - `latest`

### Push targets
- Internal private registry (login handled by job type)
  - Registry: `$DOCKER_REPOSITORY_URL` (internal jobs)
  - Example path: `docker.tool.reorc.cloud/<image_name>:<tags>`

- Public Docker Hub (public jobs)
  - Namespace: `recurvedata/<image_name>:<tags>`

- Aliyun Container Registry (pushed in addition for all Docker build jobs)
  - Registry: `reorc-registry-cn-registry-vpc.cn-shenzhen.cr.aliyuncs.com`
  - Namespace mapping:
    - Non-production (test/staging): `internal`
    - Production: `public`
  - Full path: `<registry>/<namespace>/<image_name>:<tags>`

### Login and authentication
Templates in `.gitlab/ci/templates.yml`:
- `.docker_internal_configuration`: login to internal private registry and also login to Aliyun
- `.docker_public_configuration`: login to Docker Hub and also login to Aliyun

Both templates execute `docker logout || true` once in `before_script`, then log in to the respective registry and Aliyun so a single job can push to multiple registries.

### Required CI variables (examples)
Configure the following as Masked/Protected variables in GitLab CI/CD settings:

```text
# Nexus / PyPI
NEXUS_USERNAME, NEXUS_PASSWORD, NEXUS_REPOSITORY_URL, NEXUS_PACKAGE_URL
PYPI_USERNAME, PYPI_PASSWORD, PYPI_REPOSITORY_URL (optional)

# Private registry (internal jobs)
DOCKER_REPOSITORY_URL, DOCKER_USERNAME, DOCKER_PASSWORD

# Docker Hub (public jobs)
DOCKER_OFFICIAL_REPOSITORY_URL, DOCKER_OFFICIAL_USERNAME, DOCKER_OFFICIAL_PASSWORD

# Aliyun registry (additional push in all Docker jobs)
ALIYUN_REGISTRY_URL=reorc-registry-cn-registry-vpc.cn-shenzhen.cr.aliyuncs.com
ALIYUN_USERNAME, ALIYUN_PASSWORD

# Namespaces declared in repo variables (adjust if needed)
ALIYUN_NAMESPACE_INTERNAL=internal
ALIYUN_NAMESPACE_PUBLIC=public
```

### Manual triggers and verification
- On the main branch, `package_python_public` and `build_docker_public` are manual; click “Play” in the GitLab Pipeline UI.
- Verify images:
  - Internal: `docker.tool.reorc.cloud/<image_name>:<tag>`
  - Docker Hub: `recurvedata/<image_name>:<tag>`
  - Aliyun: `reorc-registry-cn-registry-vpc.cn-shenzhen.cr.aliyuncs.com/<namespace>/<image_name>:<tag>`
