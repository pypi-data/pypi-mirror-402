#!/bin/bash

#abort at first error
set -e

name=libsan

if [[ "$#" != "1" ]]; then
    #get the last tag and increment minor version
    version=$(git describe --tags  | gawk -F"." '{$NF+=1}{print $0RT}' OFS="." ORS="")
else
    version=$1
fi

if [[ ! $version =~ ^[[:digit:]]+.[[:digit:]]+.[[:digit:]]+$ ]]; then
    echo "Invalid version $version"
    exit 1
fi

echo "Make sure we are on master branch"
git checkout master

echo "Make sure there is no pending commit"
git diff-index --quiet HEAD

sed -i -e "s/__version__ = ".*"/__version__ = \"${version}\"/g" ${name}/__about__.py

previous_tag=$(git tag | sort --version-sort | tail -1)
changelog=$(git log --oneline --no-decorate "$previous_tag"..master .)

echo "Creating commit"
git commit -s -m "Release ${version}" -m "$changelog" ${name}/__about__.py
git push

echo "Adding tag"
git tag -a -m "Release ${version}" "${version}"
git push --tags
