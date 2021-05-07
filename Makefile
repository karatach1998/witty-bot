export DRONE_COMMIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

rundev:
	docker-compose -f docker-compose-dev.yml up --build

deploy:
	drone exec --trusted --secret-file .drone_secrets .drone.yml
