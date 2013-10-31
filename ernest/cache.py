from werkzeug.contrib.cache import MemcachedCache, NullCache


class CacheConfigError(Exception):
    pass


def build_cache(config):
    """Sets up cache based on settings

    memcached:

        MEMCACHE_URL
        MEMCACHE_PREFIX (optional)

    """
    if config.get('MEMCACHE_URL'):
        return MemcachedCache(
            # FIXME - if app.config.get some non-string, this fails
            servers=config.get('MEMCACHE_URL').split(','),
            key_prefix=config.get('MEMCACHE_PREFIX', 'ernest:'))

    print 'Using NullCache().'
    return NullCache()
