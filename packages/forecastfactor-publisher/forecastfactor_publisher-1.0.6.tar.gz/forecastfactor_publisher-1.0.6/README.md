# Forecast Factor Publisher

A Python library for publishing forecast data to the Forecast Factor API. This package provides a simple interface to upload time series data, forecasts, and associated metadata to the forecast ingestion service.

## Features

- Upload raw time series data with metadata
- Publish forecast data with confidence bounds
- Include model information and performance metrics
- Support for turning points analysis
- Comprehensive error handling and validation

## Installation

### From PyPI (Recommended)

```bash
pip install forecastfactor-publisher
```

### From Source

```bash
git clone <repository-url>
cd forecastfactor_publisher
pip install -e .
```

## Quick Start

```python
import pandas as pd
from forecastfactor_publisher import forecastfactor_publish

# Prepare your data
raw_data = pd.DataFrame({
    'date': ['2023-01-01', '2023-01-02'],
    'value': [100, 110]
})

forecast_data = pd.DataFrame({
    'date': ['2023-02-01', '2023-02-02'],
    'value': [120, 130]
})

forecast_bounds = pd.DataFrame({
    'date': ['2023-02-01', '2023-02-02'],
    'lb95': [115, 125],
    'ub95': [125, 135]
})

forecast_residuals = pd.DataFrame({
    'date': ['2023-01-01', '2023-01-02'],
    'value': [0.1, -0.2]
})

# Define metadata
turning_points = {
    "2023-01-15": ["peak", "trough"],
    "2023-02-01": ["peak"]
}

metadata = {
    "source": "internal_data",
    "description": "Monthly sales forecast"
}

model_inputs = {
    "algorithm": "ARIMA",
    "mae": "0.15",
    "rmse": "0.23"
}

model_info = {
    "parameters": ["p=1", "d=1", "q=1"],
    "features": ["lag_1", "trend"]
}

# Optionally, you can specify a custom API endpoint:
# result = forecastfactor_publish(..., base_url="https://your-custom-api-endpoint")

# Or choose between dev and prod environments:
# result = forecastfactor_publish(..., environment="dev")  # Uses dev-forecastfactor-ingestor
# result = forecastfactor_publish(..., environment="prod") # Uses forecastfactor-ingestor (default)

# Publish to API
result = forecastfactor_publish(
    api_key="your_api_key_here",
    group_name="sales_forecasts",
    series_name="monthly_sales",
    model_name="arima_111",
    transformation_name="none",
    data_frequency="monthly",
    raw_data=raw_data,
    forecast_data=forecast_data,
    forecast_bounds=forecast_bounds,
    forecast_residuals=forecast_residuals,
    turning_points=turning_points,
    metadata=metadata,
    model_inputs=model_inputs,
    model_info=model_info
)

print(result)

# Example with different environment configurations:
print("\n--- Environment Examples ---")

# Use production environment (default)
result_prod = forecastfactor_publish(
    api_key="your_api_key_here",
    group_name="sales_forecasts",
    series_name="monthly_sales",
    model_name="arima_111",
    transformation_name="none",
    data_frequency="monthly",
    raw_data=raw_data,
    forecast_data=forecast_data,
    forecast_bounds=forecast_bounds,
    forecast_residuals=forecast_residuals,
    turning_points=turning_points,
    metadata=metadata,
    model_inputs=model_inputs,
    model_info=model_info,
    environment="prod"  # Explicitly set production (default)
)

# Use development environment
result_dev = forecastfactor_publish(
    api_key="your_api_key_here",
    group_name="sales_forecasts",
    series_name="monthly_sales",
    model_name="arima_111",
    transformation_name="none",
    data_frequency="monthly",
    raw_data=raw_data,
    forecast_data=forecast_data,
    forecast_bounds=forecast_bounds,
    forecast_residuals=forecast_residuals,
    turning_points=turning_points,
    metadata=metadata,
    model_inputs=model_inputs,
    model_info=model_info,
    environment="dev"  # Use development environment
)

# Use custom endpoint (overrides environment setting)
result_custom = forecastfactor_publish(
    api_key="your_api_key_here",
    group_name="sales_forecasts",
    series_name="monthly_sales",
    model_name="arima_111",
    transformation_name="none",
    data_frequency="monthly",
    raw_data=raw_data,
    forecast_data=forecast_data,
    forecast_bounds=forecast_bounds,
    forecast_residuals=forecast_residuals,
    turning_points=turning_points,
    metadata=metadata,
    model_inputs=model_inputs,
    model_info=model_info,
    base_url="https://your-custom-endpoint.com"  # Custom endpoint
)
```

## API Reference

### `forecastfactor_publish()`

Posts time series data and metadata to the Forecast Factor API.

#### Parameters

- **api_key** (str): API key for authentication
- **group_name** (str): The name of the group the series belongs to
- **series_name** (str): The name of the series
- **model_name** (str): The name of the model
- **transformation_name** (str): The transformation applied to the original dataset (e.g., 'none', 'log')
- **data_frequency** (str): The series data frequency (monthly, weekly, daily, etc.)
- **raw_data** (pd.DataFrame): DataFrame with columns ['date', 'value']
- **forecast_data** (pd.DataFrame): DataFrame with columns ['date', 'value']
- **forecast_bounds** (pd.DataFrame): DataFrame with columns ['date', 'lb95', ..., 'ub95']
- **forecast_residuals** (pd.DataFrame): DataFrame with columns ['date', 'value']
- **turning_points** (Dict): Dictionary where keys are timestamps, values are lists of turning points
- **metadata** (Dict): Additional metadata characterizing the series
- **model_inputs** (Dict): Information about the forecasting model and performance metrics
- **model_info** (Dict): Dictionary where keys are model parameters, values are lists of values
- - **base_url** (str, optional): Override the default API endpoint URL. Defaults to the official endpoint.
- **environment** (str, optional): Choose between 'dev' and 'prod' environments. Defaults to 'prod'.

#### Returns

- **Dict**: Response from the API with status and message

## Development

### Prerequisites

- Python 3.7 or higher
- pip
- twine (for publishing)

### Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd forecastfactor_publisher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

## Publishing New Versions

### Step 1: Update Version Number

Before publishing a new version, you must update the version number in `setup.py`:

```python
# In setup.py, line 5
version="0.1.9",  # Increment this version number
```

**Version Numbering Convention:**
- **Major.Minor.Patch** (e.g., 1.2.3)
- **Major**: Breaking changes
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, backward compatible

### Step 2: Update Changelog (Optional but Recommended)

Create or update a `CHANGELOG.md` file to document changes:

```markdown
# Changelog

## [0.1.9] - 2024-01-15
### Added
- New feature X
- Enhanced error handling

### Fixed
- Bug fix Y

## [0.1.8] - 2024-01-01
### Added
- Initial release
```

### Step 3: Commit Changes

```bash
git add .
git commit -m "Bump version to 0.1.9"
git tag v0.1.9
git push origin main
git push origin v0.1.9
```

### Step 4: Build and Publish

Use the provided release script:

```bash
# Make sure you're in the project root directory
./release.sh
```

Or manually:

```bash
# Clean old builds
rm -rf build dist *.egg-info

# Create new build
python3 setup.py sdist bdist_wheel

# Upload to PyPI
twine upload dist/*
```

### Step 5: Verify Publication

Check that your package is available on PyPI:

```bash
pip install --upgrade forecastfactor-publisher
```

## Configuration

### PyPI Credentials

Before publishing, ensure you have PyPI credentials configured:

```bash
# Create ~/.pypirc file
[distutils]
index-servers =
    pypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = your_username
password = your_password
```

Or use environment variables:

```bash
export TWINE_USERNAME=your_username
export TWINE_PASSWORD=your_password
```

## Testing

### Local Testing

```bash
# Install in development mode
pip install -e .

# Test the package
python -c "from forecastfactor_publisher import forecastfactor_publish; print('Package imported successfully')"
```

### Test PyPI (Optional)

For testing before publishing to production PyPI:

```bash
# Upload to test PyPI first
twine upload --repository testpypi dist/*

# Install from test PyPI
pip install --index-url https://test.pypi.org/simple/ forecastfactor-publisher
```

## Troubleshooting

### Common Issues

1. **Version Already Exists**: If you get an error about the version already existing, increment the version number in `setup.py`.

2. **Authentication Failed**: Ensure your PyPI credentials are correct in `~/.pypirc` or environment variables.

3. **Build Errors**: Make sure all dependencies are installed and the package structure is correct.

4. **Import Errors**: Verify that `__init__.py` files are present in all directories.

### Getting Help

If you encounter issues:

1. Check the [PyPI documentation](https://packaging.python.org/)
2. Verify your package structure matches Python packaging standards
3. Test locally before publishing