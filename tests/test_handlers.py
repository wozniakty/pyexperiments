from datetime import datetime
from functools import partial
from functools import reduce
from functools import wraps
from typing import Type

import pytest


def add_logger(next, request, *deps):
    print("Starting")
    result = next(print, request, *deps)
    print("Ending")
    return result


def add_auth(next, *deps):
    claims = {"sub": "a"}
    return next(claims, *deps)


def add_metrics(next, *deps):
    mets = lambda name, m: print(f"Metric {name}: {m}")
    return next(mets, *deps)


def add_no_dep(next, *deps):
    print("just checking something")
    return next(*deps)


def create_handler(*funcs):
    handler = reduce(lambda a, b: partial(b, a), reversed(funcs))
    return handler


def create_contract(*funcs):
    return partial(create_handler, *funcs)


def wrapped(*dependencies):
    def decorator(handler):
        chain = [handler, *reversed(dependencies)]

        @wraps(handler)
        def wrapped_handler(*args, **kwargs):
            return reduce(lambda a, b: partial(b, a), chain)(*args, **kwargs)

        return wrapped_handler

    return decorator


def test_it():
    req = {"IsA": "Request"}

    def handler(claims, log, metrics, request):
        log("Calling the handler")
        metrics("Called", 1)
        log(claims)
        log(request)
        return request

    view = create_handler(add_metrics, add_logger, add_auth, add_no_dep, handler)

    assert view(req) == req


def test_it_decorator():
    req = {"IsA": "Request"}

    @wrapped(add_metrics, add_logger, add_auth, add_no_dep)
    def handler(claims, log, metrics, request):
        log("Calling the handler")
        metrics("Called", 1)
        log(claims)
        log(request)
        return request

    assert handler(req) == req


def test_decorator_contract():
    req = {"IsA": "Request"}

    my_dependencies = wrapped(add_metrics, add_logger, add_auth, add_no_dep)

    @my_dependencies
    def handler(claims, log, metrics, request):
        log("Calling the handler")
        metrics("Called", 1)
        log(claims)
        log(request)
        return request

    assert handler(req) == req


def test_it_with_extra_params():
    req = {"IsA": "Request"}

    def handler(claims, log, metrics, request, org_id, group_id=None):
        log("Calling the handler")
        metrics("Called", 1)
        log(claims)
        log(request)
        return request, org_id, group_id

    view = create_handler(add_metrics, add_logger, add_auth, add_no_dep, handler)

    assert view(req, 1) == (req, 1, None)
    assert view(req, 1, 2) == (req, 1, 2)


def test_it_fail():
    req = {"IsA": "Request"}

    def handler(request):
        return request

    view = create_handler(add_metrics, add_logger, add_auth, add_no_dep, handler)
    with pytest.raises(TypeError):
        result = view(req)


def test_contract():
    def handler1(metrics, request):
        metrics("a", 1)
        return request

    def handler2(claims, metrics, request):
        metrics("a", 1)
        return request, claims

    unauthed_handler_contract = create_contract(add_metrics)
    authorized_handler_contract = create_contract(add_metrics, add_auth)

    unauthed_handler = unauthed_handler_contract(handler1)
    authorized_handler = authorized_handler_contract(handler2)

    assert unauthed_handler(10) == 10
    assert authorized_handler(10) == (10, {"sub": "a"})
