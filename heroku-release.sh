
app_name=$1
shift 1
dyno_types=$@

updates=$(
    for dt in $dyno_types; do
	image_id=$(docker inspect registry.heroku.com/$app_name/$dt:latest --format={{.Id}})
	printf ', %s' '{"type": "'"$dt"'", "docker_image": "'"$image_id"'"}'
    done)
updates=${updates:2}

echo "Releasing images ${dyno_types// /,} for $app_name"

http --ignore-stdin --check-status -v\
     PATCH https://api.heroku.com/apps/$app_name/formation \
     "Accept: application/vnd.heroku+json; version=3.docker-releases" \
     "Authorization: Bearer $HEROKU_AUTH_TOKEN" \
     updates:="[$updates]"
exit $?
