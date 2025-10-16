# kartoteka

git pull

sudo docker compose up --build

then Ctrl+C to stop logging

check if containers are running
sudo docker ps

if not 
start in dettached mode
sudo docker-compose up -d

initialize and migrate db to create all tables (run only once)
sudo docker-compose run --rm web flask db init
sudo docker-compose run --rm web flask db migrate -m "Initial migration"

upgrade db
sudo docker-compose run --rm web flask db upgrade



sudo docker-compose down --volumes --remove-orphans
