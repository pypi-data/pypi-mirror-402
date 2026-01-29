## Django ORM Query Optimization

### Preventing N+1 Queries
- **select_related**: Use for ForeignKey and OneToOne (follows forward relationships via SQL JOIN)
```python
# Good: 1 query
posts = Post.objects.select_related('author', 'category').all()

# Bad: N+1 queries
posts = Post.objects.all()
for post in posts:
    print(post.author.name)  # New query each time
```

- **prefetch_related**: Use for ManyToMany and reverse ForeignKey (separate query + Python join)
```python
# Good: 2 queries
posts = Post.objects.prefetch_related('tags', 'comments').all()

# Bad: N+1 queries
posts = Post.objects.all()
for post in posts:
    print(post.tags.all())  # New query each time
```

- **Prefetch Object**: For complex prefetch scenarios with filtering
```python
from django.db.models import Prefetch

Post.objects.prefetch_related(
    Prefetch('comments', queryset=Comment.objects.filter(is_approved=True))
)
```

### Selecting Only Required Data
- **only()**: Fetch only specified fields (creates deferred model)
```python
User.objects.only('id', 'username', 'email')
```

- **defer()**: Exclude specified fields (fetch everything except these)
```python
User.objects.defer('bio', 'profile_picture')
```

- **values()**: Return dictionaries instead of model instances (lighter)
```python
User.objects.values('id', 'username')  # Returns [{'id': 1, 'username': '...'}]
```

- **values_list()**: Return tuples (even lighter)
```python
User.objects.values_list('id', 'username')  # Returns [(1, '...), ...]
User.objects.values_list('username', flat=True)  # Returns ['user1', 'user2']
```

### Aggregation and Annotation
- **aggregate()**: Compute values across entire queryset
```python
from django.db.models import Count, Avg, Sum
Post.objects.aggregate(total=Count('id'), avg_views=Avg('view_count'))
```

- **annotate()**: Add computed fields to each object
```python
Post.objects.annotate(comment_count=Count('comments'))
```

- **F expressions**: Reference field values in database operations
```python
from django.db.models import F
Post.objects.update(view_count=F('view_count') + 1)  # Atomic increment
```

- **Q objects**: Build complex queries with AND/OR/NOT logic
```python
from django.db.models import Q
Post.objects.filter(Q(status='published') | Q(author=request.user))
```

### Query Optimization
- **exists()**: Check existence without fetching data
```python
if User.objects.filter(email=email).exists():  # Better than count() or len()
```

- **count()**: Database-level count (don't use `len(queryset)`)
```python
Post.objects.filter(status='published').count()
```

- **iterator()**: For large querysets to reduce memory usage
```python
for user in User.objects.iterator(chunk_size=1000):
    process_user(user)
```

- **bulk_create()**: Insert multiple objects in single query
```python
Post.objects.bulk_create([Post(...), Post(...), Post(...)])
```

- **bulk_update()**: Update multiple objects efficiently
```python
Post.objects.bulk_update(posts, ['status', 'updated_at'])
```

- **update()**: Database-level update (faster than save())
```python
Post.objects.filter(author=user).update(status='archived')
```

- **delete()**: Database-level delete (faster than deleting instances)
```python
Post.objects.filter(created_at__lt=cutoff_date).delete()
```

### Indexing
- Add `db_index=True` to fields used in:
  - WHERE clauses (`filter()`, `exclude()`)
  - ORDER BY clauses (`order_by()`)
  - JOIN operations (ForeignKey automatically indexed)
- Use composite indexes in Meta `indexes` for multi-field queries

### Transactions
- **Atomic Operations**: Wrap related changes in transaction
```python
from django.db import transaction

with transaction.atomic():
    user.balance -= amount
    user.save()
    Transaction.objects.create(user=user, amount=amount)
```

- **select_for_update()**: Lock rows for update (prevent race conditions)
```python
with transaction.atomic():
    user = User.objects.select_for_update().get(id=user_id)
    user.balance -= amount
    user.save()
```

### Caching Strategies
- **cached_property**: Cache expensive model method results
```python
from django.utils.functional import cached_property

class Post(models.Model):
    @cached_property
    def comment_count(self):
        return self.comments.count()
```

- **Query Caching**: Use Django cache framework for expensive queries
- **Database Query Cache**: PostgreSQL query cache or Redis for query results

### Raw SQL and Performance
- **raw()**: Execute raw SQL returning model instances
```python
Post.objects.raw('SELECT * FROM app_post WHERE view_count > %s', [1000])
```

- **extra()**: Add custom SQL to queryset (avoid if possible, use annotate)
- **connection.cursor()**: Direct database access (last resort)

### SQL Injection Prevention
- Always use ORM methods or parameterized queries
- Use `%s` placeholders with raw SQL, never string formatting
- Never use f-strings or `.format()` with user input in SQL
- Never use `extra(where=[f"field={user_input}"])`

### Debugging Queries
- **Django Debug Toolbar**: Install for query analysis in development
- **QuerySet.query**: View generated SQL with `print(queryset.query)`
- **connection.queries**: Access all queries in DEBUG mode
```python
from django.db import connection
print(len(connection.queries))  # Number of queries
print(connection.queries)  # List of executed queries
```

### Best Practices
- Profile queries in production to identify slow queries
- Use `explain()` to analyze query execution plans
- Avoid filtering in Python when you can filter in database
- Use database-level operations (update, delete) instead of loading into memory
- Understand lazy evaluation: QuerySets are only evaluated when needed
