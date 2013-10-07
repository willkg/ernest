from werkzeug.contrib.cache import MemcachedCache, NullCache


class CacheConfigError(Exception):
    pass


def build_cache(config):
    """Sets up cache based on settings

    memcached:

        MEMCACHE_URL
        MEMCACHE_PREFIX (optional)

    nullcache:

        NULLCACHE

    """
    if config.get('MEMCACHE_URL'):
        return MemcachedCache(
            # FIXME - if app.config.get some non-string, this fails
            servers=config.get('MEMCACHE_URL').split(','),
            key_prefix=config.get('MEMCACHE_PREFIX', 'ernest:'))

    if config.get('NULLCACHE'):
        return NullCache()

    raise CacheConfigError('No cache is configured. See settings.py.')
