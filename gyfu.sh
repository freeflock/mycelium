#!/bin/bash

TAG=0.2
NO_CACHE="false"

# requires a docker-container buildx driver
BUILD_OPTIONS="--platform linux/arm64/v8,linux/amd64 --push"
if [ "$NO_CACHE" = true ]; then
    BUILD_OPTIONS+=" --no-cache=true"
    echo "building without cache"
else
    echo "building with cache"
fi

docker buildx build $BUILD_OPTIONS -f docker/symbiosis/Dockerfile -t josiahdc/symbiosis:"${TAG}" .
docker buildx build $BUILD_OPTIONS -f docker/spread/Dockerfile -t josiahdc/spread:"${TAG}" .
