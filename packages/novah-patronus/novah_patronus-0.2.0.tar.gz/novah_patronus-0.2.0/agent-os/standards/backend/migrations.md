## Django Migration Best Practices

### Creating Migrations
- **makemigrations**: Generate migrations after model changes
```bash
python manage.py makemigrations
python manage.py makemigrations app_name  # Specific app
```

- **Review Generated Migrations**: Always review before committing
- **Descriptive Names**: Use `--name` flag for custom names
```bash
python manage.py makemigrations --name add_user_status_field
```

### Migration Structure
- **Small, Focused Changes**: One logical change per migration
- **Automatic Naming**: Let Django auto-name unless custom name adds clarity
- **Dependencies**: Django handles dependencies automatically via `dependencies` list

### Data Migrations
- **Create Empty Migration**: For data-only changes
```bash
python manage.py makemigrations --empty app_name --name populate_default_roles
```

- **RunPython**: Use for custom data operations
```python
from django.db import migrations

def populate_roles(apps, schema_editor):
    Role = apps.get_model('app_name', 'Role')
    Role.objects.bulk_create([
        Role(name='admin'),
        Role(name='user'),
    ])

def reverse_populate(apps, schema_editor):
    Role = apps.get_model('app_name', 'Role')
    Role.objects.filter(name__in=['admin', 'user']).delete()

class Migration(migrations.Migration):
    dependencies = [('app_name', '0001_initial')]

    operations = [
        migrations.RunPython(populate_roles, reverse_populate),
    ]
```

- **Access Models**: Always use `apps.get_model()` in data migrations (never import models directly)
- **Reversible**: Provide reverse operation for all data migrations

### Schema Changes Best Practices

**Adding Fields:**
- Make new fields nullable OR provide default values
```python
# Good: nullable field
field = models.CharField(max_length=100, null=True, blank=True)

# Good: field with default
field = models.CharField(max_length=100, default='')
```

**Removing Fields:**
- Step 1: Deploy code that doesn't use the field
- Step 2: Create migration to remove field
- Step 3: Deploy migration

**Renaming Fields:**
- Use `migrations.RenameField()` for Django to detect rename
- Alternative: Add new field → migrate data → remove old field (safer for large tables)

**Changing Field Types:**
- Risky for large tables, consider: add new field → migrate data → remove old field
- Test with production-like data volumes

### Zero-Downtime Migrations
- **Backwards Compatible**: Ensure code works before AND after migration
- **Deployment Order**:
  1. Deploy migration that adds field (with null=True or default)
  2. Deploy code using new field
  3. (Optional) Create migration to make field non-nullable if needed

- **Avoid**:
  - Renaming columns in production without compatibility layer
  - Removing fields still used by running code
  - Adding non-nullable fields without defaults

### Index Management
- **Concurrent Index Creation**: Use for PostgreSQL to avoid locks
```python
from django.contrib.postgres.operations import AddIndexConcurrently

class Migration(migrations.Migration):
    atomic = False  # Required for concurrent operations

    operations = [
        AddIndexConcurrently(
            model_name='post',
            index=models.Index(fields=['status', 'created_at'], name='post_status_idx'),
        ),
    ]
```

- **Large Tables**: Create indexes during low-traffic periods
- **Test Performance**: Ensure index actually improves query performance

### Migration Conflicts
- **Detection**: Django detects conflicting migrations automatically
- **Resolution**: Use `python manage.py makemigrations --merge`
- **Prevention**: Pull latest migrations before creating new ones

### Squashing Migrations
- **Purpose**: Consolidate many migrations into one
```bash
python manage.py squashmigrations app_name 0004
```
- **When**: When you have 50+ migrations in an app
- **Caution**: Only squash migrations already deployed to production

### Testing Migrations
- **Test Both Directions**: Test forward and reverse migrations
```bash
python manage.py migrate app_name 0003  # Forward to 0003
python manage.py migrate app_name 0002  # Reverse to 0002
```

- **Test with Real Data**: Use production-like dataset for testing
- **Check SQL**: Review generated SQL
```bash
python manage.py sqlmigrate app_name 0001
```

### Migration Commands
```bash
# Show migration status
python manage.py showmigrations

# Show migration status for specific app
python manage.py showmigrations app_name

# Migrate to specific migration
python manage.py migrate app_name 0003

# Reverse all migrations for app
python manage.py migrate app_name zero

# Show SQL for migration
python manage.py sqlmigrate app_name 0001

# Check for migration issues
python manage.py makemigrations --check --dry-run
```

### Version Control
- ✅ Always commit migrations to version control
- ✅ Keep migrations in order (don't skip numbers)
- ❌ Never modify migrations after they're merged to main branch
- ❌ Never delete migrations that have been deployed
- ❌ Never reorder migrations that others have applied

### RunSQL for Complex Operations
```python
migrations.RunSQL(
    sql="CREATE INDEX CONCURRENTLY idx_name ON table_name (column)",
    reverse_sql="DROP INDEX CONCURRENTLY idx_name",
    state_operations=[...]  # Model state operations
)
```

### Best Practices Summary
1. Always review auto-generated migrations before committing
2. Test migrations locally with production-like data
3. Provide reverse operations for all migrations when possible
4. Never modify deployed migrations (create new one instead)
5. Use data migrations for data changes, schema migrations for schema changes
6. For large tables, consider online schema change tools (pt-online-schema-change, gh-ost)
7. Keep migrations small and focused
8. Use meaningful migration names for data migrations
9. Document complex migrations with comments
