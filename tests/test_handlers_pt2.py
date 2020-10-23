from functools import partial
from functools import reduce


def compose_handler(wrappers, dependencies, handler):
    def call(*args, **kwargs):
        wrapped_handler = reduce(
            lambda a, b: partial(b, a), [handler, *reversed(wrappers)]
        )
        return wrapped_handler(
            *[dep(*args, **kwargs) for dep in dependencies], *args, **kwargs
        )

    return call


def test_compose():
    metrics = {}

    def log_metrics(next, claims, request, organization_id, *args, **kwargs):
        metrics[f"start-{organization_id}-{request}"] = 1
        result = next(claims, request, organization_id, *args, **kwargs)
        metrics[f"end-{organization_id}-{request}"] = 2
        return result

    def claims_dep(request, organization_id, group_id):
        return {"org_id": organization_id, "group_id": group_id}

    def do_thing(claims, request, organization_id, group_id):
        assert claims == {"org_id": 1, "group_id": 10}
        return f"Successful {request} {organization_id} {group_id}"

    handler = compose_handler([log_metrics], [claims_dep], do_thing)

    result = handler("areq", 1, 10)

    assert result == "Successful areq 1 10"
    assert metrics["start-1-areq"] == 1
    assert metrics["end-1-areq"] == 2


def test_compose_contract():
    metrics = {}

    def log_metrics(next, claims, request, organization_id, *args, **kwargs):
        metrics[f"start-{organization_id}-{request}"] = 1
        result = next(claims, request, organization_id, *args, **kwargs)
        metrics[f"end-{organization_id}-{request}"] = 2
        return result

    def claims_dep(request, organization_id, group_id):
        return {"org_id": organization_id, "group_id": group_id}

    def do_thing(claims, request, organization_id, group_id):
        assert claims == {"org_id": 1, "group_id": 10}
        return f"Successful {request} {organization_id} {group_id}"

    api_contract = partial(compose_handler, [log_metrics], [claims_dep])
    handler = api_contract(do_thing)

    result = handler("areq", 1, 10)

    assert result == "Successful areq 1 10"
    assert metrics["start-1-areq"] == 1
    assert metrics["end-1-areq"] == 2
