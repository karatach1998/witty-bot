export DRONE_COMMIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

rundev:
	docker-compose -f docker-compose-dev.yml build
	docker-compose -f docker-compose-dev.yml up

deploy:
	drone exec --trusted --secret-file .drone_secret .drone.yml
