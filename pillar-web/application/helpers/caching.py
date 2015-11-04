from application import app
from application import redis_client

from flask.ext.login import current_user
from flask.ext.cache import make_template_fragment_key


def make_redis_cache_key(cache_prefix, category=''):
    """Utility to build a redis cache key, to be use for filtering."""
    user_id = 'ANONYMOUS'
    if current_user.is_authenticated():
        user_id = current_user.string_id
    cache_key = make_template_fragment_key(cache_prefix,
        vary_on=[user_id, category])
    # Add prefix to the cache key and a *
    return '{0}{1}*'.format(app.config['CACHE_KEY_PREFIX'], cache_key)


def delete_redis_cache_keys(cache_prefix, category=''):
    """Delete a specific cache key."""
    if not redis_client:
        return
    key = make_redis_cache_key(cache_prefix, category)
    keys_list = redis_client.keys(key)
    for key in keys_list: redis_client.delete(key)


def delete_redis_cache_template(template_item, uuid, user_id=None, all_users=True):
    """Delete a redis cached template fragment. Supports various options for
    filtering the right keys.

    :type template_item: string
    :param template_item: Prefix for the template, e.g. 'node_view'

    :type uuid: string
    :param uuid: The unique identifier for the item displayed in the template.
        Usually the string version of the Node ObjectID.

    :type user_id: string
    :param user_id: User ID cache, use for filtering per-user caches (useful to
        display cached rating pages)
    """
    if all_users:
        cache_key = make_template_fragment_key(template_item,
            vary_on=[uuid])
    else:
        if user_id:
            user_id = str(user_id)
        else:
            if current_user.is_authenticated():
                user_id = current_user.string_id
            else:
                user_id = "ANONYMOUS"

        cache_key = make_template_fragment_key(template_item,
            vary_on=[uuid, user_id])

    # Add prefix to the cache key
    if not redis_client:
        return
    key = '{0}{1}*'.format(app.config['CACHE_KEY_PREFIX'], cache_key)
    keys_list = redis_client.keys(key)
    for key in keys_list: redis_client.delete(key)

