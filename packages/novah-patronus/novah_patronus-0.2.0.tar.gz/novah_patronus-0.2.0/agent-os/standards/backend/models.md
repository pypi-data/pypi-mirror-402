## Django Model Best Practices

### Naming and Structure
- **Model Names**: Use singular PascalCase (e.g., `User`, `BlogPost`, `OrderItem`)
- **Field Names**: Use snake_case (e.g., `created_at`, `is_active`, `user_email`)
- **Timestamps**: Always include `created_at` and `updated_at` using `auto_now_add` and `auto_now`
- **Ordering**: Set default ordering in Meta class with `ordering` attribute

### Essential Model Methods
- **`__str__`**: Always define for readable object representation
- **`get_absolute_url`**: Define for models with detail views
- **`clean`**: Use for model-level validation logic
- **`save`**: Override carefully, always call `super().save()`, prefer signals for side effects

### Field Choices
- Use `models.TextChoices` or `models.IntegerChoices` for field choices (Django 3.0+)
- Define choices as nested class within the model
```python
class Status(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PUBLISHED = 'published', 'Published'
```

### Relationships
- **ForeignKey**: Always set `on_delete` explicitly (CASCADE, PROTECT, SET_NULL, etc.)
- **Related Names**: Always define `related_name` for clarity (use `'+'` to disable reverse relation)
- **ManyToMany**: Use `through` model when you need extra fields on the relationship

### Data Integrity
- Use `blank=False, null=False` by default (be explicit about optionality)
- Use database constraints: `unique=True`, `unique_together`, `db_index=True`
- Use `validators` list for field-level validation
- Use Meta `constraints` for complex database-level rules (CheckConstraint, UniqueConstraint)

### Abstract Base Models
- Create abstract base models for common fields (timestamps, soft deletes)
```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

### Custom Managers and QuerySets
- Use custom managers for reusable query logic
- Chain QuerySet methods instead of custom methods on manager
- Use `objects` for default manager, create additional managers as needed (e.g., `active_objects`)

### Performance
- Add `db_index=True` on fields used in filtering/ordering
- For query optimization, see `standards/backend/queries.md`
- Avoid storing computed values unless performance requires it

### Meta Options
- Set `verbose_name` and `verbose_name_plural` for admin readability
- Use `ordering` for default sort order
- Define `indexes` for composite indexes
- Use `constraints` for database-level validation

### Avoid
- Don't put business logic in models (see `standards/global/conventions.md` for service layer)
- Don't use signals excessively (prefer explicit calls)
- Don't override `__init__` (use `from_db` or `__new__` if needed)
- Avoid generic foreign keys unless absolutely necessary
