#!/bin/bash -e

ENV_BRANCH=${1?Must specify the branch for an env file}
ENV_FILE="env-$ENV_BRANCH.tpl"
[[ -f "$ENV_FILE" ]] || { echo "no file $ENV_FILE" ; exit 2 ; }
pushd pipeline
uav merge --pipeline fbnconfig.pipeline.tpl --directory templates "../$ENV_FILE" -o .pipeline.yml
popd
# to login run below
#fly -t client-engineering login -n client-engineering -c https://concourse.finbourne.com
if [[ "$ENV_BRANCH" == "master" ]] ; then
    fly -t client-engineering set-pipeline --config pipeline/.pipeline.yml --pipeline fbnconfig
else
    fly -t client-engineering set-pipeline --config pipeline/.pipeline.yml --pipeline "fbnconfig-$ENV_BRANCH"
fi
