
ROOT="$(dirname "$(readlink -f "$0")")"

ASSETS="$ROOT/pillar-web/application/static/assets/"
TEMPLATES="$ROOT/pillar-web/application/templates/"

cd $ROOT
if [ $(git rev-parse --abbrev-ref HEAD) != "production" ]; then
    echo "You are NOT on the production branch, refusing to rsync_ui." >&2
    exit 1
fi

echo "\n *** GULPA GULPA ***\n"
if [ -x ./node_modules/.bin/gulp ]; then
    ./node_modules/.bin/gulp
else
    gulp
fi

echo "\n *** SYNCING ASSETS ***\n"
rsync -avh $ASSETS root@cloudapi.blender.org:/data/git/pillar-web/pillar-web/application/static/assets/

echo "\n *** SYNCING TEMPLATES *** \n"
rsync -avh $TEMPLATES root@cloudapi.blender.org:/data/git/pillar-web/pillar-web/application/templates/
