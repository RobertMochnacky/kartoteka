# kartoteka

Pull changes from Github repo

```git pull```

```sudo docker compose up --build```

then Ctrl+C to stop logging

check if containers are running:
```sudo docker ps```

if not 
start in dettached mode:

```sudo docker-compose up -d```

initialize db to create all tables (run only once)

```sudo docker-compose run --rm web flask db init```

Migrate db to reflect changes in tables columns:

```sudo docker-compose run --rm web flask db migrate -m "Change: "```

If no change has been detected, manually update db via migration plan:
1. Create a blank migration file

```sudo docker-compose run --rm web flask db revision -m "Add theme column to User"```

2. Edit the migration file manually

```
def upgrade():
    # Add theme column
    op.add_column('users', sa.Column('theme', sa.String(length=10), nullable=False, server_default='light'))

def downgrade():
    # Remove theme column
    op.drop_column('users', 'theme')
```

Upgrade db

```sudo docker-compose run --rm web flask db upgrade```

Changes made to the code - Rebuild and restart:

```sudo docker-compose down```
```sudo docker-compose up --build```

Remove containers, volumes and orhpaned containers (only if needed to cleanup everything)

```sudo docker-compose down --volumes --remove-orphans```
