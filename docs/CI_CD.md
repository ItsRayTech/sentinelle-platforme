# CI/CD Pipeline Documentation

This project uses **GitHub Actions** to ensure code quality and deployment readiness.

## 🔄 Workflow: `.github/workflows/ci.yml`

Every time you push code to `main` or create a Pull Request, the following jobs run:

### 1. 🧪 Test Job (`test`)
- **Environment**: Ubuntu Latest, Python 3.11
- **Steps**:
    1.  Installs dependencies from `ml/requirements.txt` and `api/requirements.txt`.
    2.  Runs **Pytest** on `api/tests/`.
- **Goal**: Catch regressions in logic before merging.

### 2. 🐳 Build Job (`build-docker`)
- **Dependency**: Runs only if `test` passes.
- **Steps**:
    1.  Builds the Docker image for the API (`Dockerfile`).
- **Goal**: Ensure the application can be containerized successfully (no missing files, syntax errors in Dockerfile).

## ✅ How to Check Build Status
1.  Go to the **Actions** tab in the GitHub repository.
2.  Click on the latest workflow run.
3.  Green checkmarks indicate success. Red crosses indicate failure (check logs).

## 🛠 Adding New Tests
Create new test files in `api/tests/` named `test_*.py`.
Example:
```python
def test_example():
    assert 1 + 1 == 2
```
They will be automatically picked up by the CI pipeline.
