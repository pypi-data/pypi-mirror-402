# ADRF Flex Fields

Flexible, dynamic fields and nested models for ADRF (Async Django REST Framework) serializers.

## Description

ADRF Flex Fields extends the Async Django REST Framework (ADRF) with powerful field expansion and dynamic serialization capabilities. This package allows you to create more flexible APIs by enabling clients to specify which fields they want to include in responses, reducing over-fetching and improving performance.

## Features

- **Dynamic Field Selection**: Allow clients to specify which fields to include/exclude
- **Nested Model Expansion**: Expand related models on-demand
- **Async Support**: Full compatibility with ADRF's async capabilities
- **Performance Optimized**: Reduce payload size and database queries
- **Easy Integration**: Drop-in replacement for standard ADRF serializers

## Installation

```bash
pip install adrf_flex_fields
```

## Quick Start

### Basic Usage

```python
from adrf_flex_fields import FlexFieldsModelSerializer
from adrf import serializers
from myapp.models import User, Profile

class UserSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']
        expandable_fields = {
            'profile': ProfileSerializer
        }

# Usage in views
class UserViewSet(AsyncModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
```

### Field Selection

Clients can control which fields are returned:

```bash
# Get only id and username
GET /api/users/?fields=id,username

# Exclude email field
GET /api/users/?omit=email

# Expand nested profile
GET /api/users/?expand=profile
```

### Advanced Features

```python
class UserSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile', 'posts']
        expandable_fields = {
            'profile': ProfileSerializer,
            'posts': (PostSerializer, {'many': True})
        }

    # Custom field filtering
    def get_field_names(self, declared_fields, info):
        field_names = super().get_field_names(declared_fields, info)
        # Custom logic here
        return field_names
```

## Requirements

- Python >= 3.8
- Django >= 4.1
- djangorestframework >= 3.14
- adrf >= 0.1.0

## Development

### Setup Development Environment

```bash
git clone https://github.com/mushota_243/adrf-flex-fields.git
cd adrf-flex-fields
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Running Tests with Coverage

```bash
pytest --cov=adrf_flex_fields --cov-report=html
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### 0.1.0 (2024-01-20)

- Initial release
- Basic field selection and expansion functionality
- Async Django REST Framework compatibility
- Property-based testing suite

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/mushota_243/adrf-flex-fields/issues) on GitHub.
