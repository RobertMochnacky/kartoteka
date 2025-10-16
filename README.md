# kartoteka

Pull changes from Github repo

```git pull```

```sudo docker compose up --build```

then Ctrl+C to stop logging

check if containers are running
```sudo docker ps```

if not 
start in dettached mode

```sudo docker-compose up -d```

initialize db to create all tables (run only once)

```sudo docker-compose run --rm web flask db init```

Migrate db to reflect changes in tables columns
```sudo docker-compose run --rm web flask db migrate -m "Cnange: "```

Upgrade db

```sudo docker-compose run --rm web flask db upgrade```

Changes made to the code - Rebuild and restart

```sudo docker-compose down```
```sudo docker-compose up --build```

Remove containers, volumes and orhpaned containers (only if needed to cleanup everything)

```sudo docker-compose down --volumes --remove-orphans```
