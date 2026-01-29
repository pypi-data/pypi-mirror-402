# QCanvas API Clients

This module provides some utilities to interact with canvas and panopto. It is only concerned with API operations
and does not provide anything for storing the data.

## Using API result caching for faster development

Set `ENABLE_API_CACHE=True` (or `1`) as an environment variable. This will store the result of each API call on disk for
re-use next time.
The cache is written to `/tmp/qcanvas_cache`.

Only use this when debugging.