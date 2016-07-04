#!/usr/bin/env bash

cd `dirname $0`
set -e

PIDF="test.pid"
BIND="0.0.0.0:7357"

# We execute this at the end of the script,
# which may be anytime due to set -e
function finish {
    echo -e "\n> Executing EXIT trap (gunicorn QUIT), return code is $?"
    if [ -f "$PIDF" ]; then
        kill -QUIT `cat $PIDF`
    fi
}

trap finish EXIT

assert_code () {
    local expected_code="$1"
    local url="$2"
    local tested_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")

    if [ "$tested_code" -eq "$expected_code" ]; then
        echo "✓ $tested_code [expected $expected_code] $url"
        return 0
    else
        echo "✗ $tested_code [expected $expected_code] $url"
        return 1
    fi
}

echo -e "\n> Serving with `which gunicorn`"
gunicorn --error-logfile=-           \
         --access-logfile=-          \
         --bind $BIND                \
         --env CONF=test.yaml        \
         --pid=$PIDF graphdash:app   \
         &
echo "Sleeping 3"
sleep 3

echo -e "\n> Testing"
assert_code 302 "http://$BIND/"
assert_code 200 "http://$BIND/tags"
assert_code 200 "http://$BIND/family/"
assert_code 200 "http://$BIND/family/cat"
assert_code 200 "http://$BIND/search?value=*"
assert_code 200 "http://$BIND/search?value=find"
assert_code 404 "http://$BIND/nonexistent"

