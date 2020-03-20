import argparse
import hashlib
import pickle

import redis
from aiohttp import ClientSession, web

REDIS_CACHE = redis.StrictRedis()

FUNC_FOR_ALL_HTTP_METHODS = {
    'GET': lambda s, x: s.get(x),
    'POST': lambda s, x: s.post(x),
    'DELETE': lambda s, x: s.delete(x),
    'PATCH': lambda s, x: s.patch(x),
    'PUT': lambda s, x: s.put(x),
}

ALL_HTTP_METHODS = list(FUNC_FOR_ALL_HTTP_METHODS.keys())
HOST_NAME = ''
EXPIRE_TIME_SEC = 600


def get_hash_of_request(method, path):
    method_hash = hashlib.sha1(method.encode()).hexdigest()
    path_hash = hashlib.sha1(path.encode()).hexdigest()
    hash = method_hash + path_hash
    return hash


async def make_request_to_host(method, path):
    async with ClientSession() as session:
        http_method = FUNC_FOR_ALL_HTTP_METHODS[method]
        async with http_method(session, HOST_NAME + '/' + path) as resp:
            return await resp.text()


async def handle_client_request(request):
    hash = get_hash_of_request(request.method, request.match_info['path'])
    if REDIS_CACHE.get(hash):
        REDIS_CACHE.expire(hash, EXPIRE_TIME_SEC)
        ans = pickle.loads(REDIS_CACHE.get(hash))
    else:
        ans = await make_request_to_host(request.method,
                                         request.match_info['path'])
        REDIS_CACHE.set(hash, pickle.dumps(ans), ex=EXPIRE_TIME_SEC)
    return web.Response(text=ans)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Proxy server app to some host.')
    parser.add_argument('--host',
                        type=str,
                        default='http://httpbin.org/',
                        help='Send request to host name.')
    args = parser.parse_args()
    HOST_NAME = args.host

    if not HOST_NAME.startswith('http://'):
        HOST_NAME = 'http://' + HOST_NAME

    app = web.Application()
    for m in ALL_HTTP_METHODS:
        app.add_routes([web.route(m, '/{path:.*}', handle_client_request)])

    web.run_app(app, host='127.0.0.1', port='5000')
