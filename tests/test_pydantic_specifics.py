import pytest
from pydantic import BaseModel
from pydantic import root_validator
from pydantic import validator
from pydantic.error_wrappers import ValidationError


def test_pydantic_validator_values():
    class M(BaseModel):
        x: str
        y: int
        z: bool

        @validator("x")
        def first_param(cls, x, values):
            assert x == "1"  # type conversion happens before validator
            assert (
                values == {}
            )  # contains only values that have already finished validating
            return x

        @validator("y")
        def second_param(cls, y, values):
            assert values == {"x": "1"}
            return y

        @validator("z", pre=True)
        def pre_validator(cls, z):
            assert z == "false"
            return z

    m = M(x=1, y="2", z="false")
    assert m.x == "1"
    assert m.y == 2
    assert m.z == False


def test_pydantic_root_validator_values():
    class M(BaseModel):
        x: str
        y: int
        z: bool

        @root_validator
        def check_values(cls, values):
            assert values == {"x": "1", "y": 2, "z": False}
            return values

    m = M(x=1, y="2", z="false", w="aaaaaa")


def test_pydantic_submodel_root_validator():
    class M(BaseModel):
        x: str = None

    class S(M):
        y: int = None

        @root_validator
        def check_for_none(cls, values):
            if not any(values.values()):
                raise ValueError("must provide at least one value")
            return values

    with pytest.raises(ValidationError) as e:
        m = S()
    assert e.value.errors()[0]["msg"] == "must provide at least one value"
    with pytest.raises(ValidationError) as e:
        m = S(x=None, y=None)
    assert e.value.errors()[0]["msg"] == "must provide at least one value"
