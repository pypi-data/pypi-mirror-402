# Django rule-engine - Field, Widget & API

This module contains custom Django fields and helper APIs for the project.

## 📦 Contents

### RuleField - Field for Rule Engine

Specialized Django field for working with `rule-engine` rules, including:
- ✨ Visual editor with syntax highlighting
- 🔍 Dynamic frontend validation
- 📝 Configurable JSON examples
- ⚡ REST API for validation

### Validation API

REST endpoint for dynamically validating rule-engine rules.

- **Endpoint:** `POST /api/validate-rule/`
- **Documentation:** [fields/README.md](fields/README.md#validation-api)

## 🚀 Quick Start

### 1. Import and Use

```python
from django_rule_engine.fields import RuleField

class MyModel(models.Model):
    rule = RuleField(
        example_data={"age": 25, "status": "active"}
    )
```

## 📚 Documentation

- 

1. **[INDEX.md](INDEX.md)** - Complete documentation index
2. **[INSTALL.md](INSTALL.md)** - Installation guide
3. **[QUICKSTART.md](QUICKSTART.md)** - Quick start (5 min)
4. **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Migration guide
5. **[EXAMPLES.md](EXAMPLES.md)** - Code examples
6. **[VISUAL_DEMO.py](VISUAL_DEMO.md)** - Demonstração Visual


## 🎯 Implementation Example

The field is already being used in the `Cohort` model in [coorte/models.py](../../coorte/models.py):

```python
class Cohort(Model):
    name = CharField("cohort name", max_length=256, unique=True)
    rule = RuleField(
        "validation rule",
        blank=True,
        null=True,
        example_data={
            "login": "user123",
            "user": {"email": "user@example.com"},
            "name": "Zé da Silva",
            "active": True
        },
        default="login == 'user123' and user.email != 'user123@example.com'",
    )

    class Meta:
        verbose_name = _("cohort")
        verbose_name_plural = _("cohorts")
        ordering = ["name"]

    def __str__(self):
        return self.name
```
