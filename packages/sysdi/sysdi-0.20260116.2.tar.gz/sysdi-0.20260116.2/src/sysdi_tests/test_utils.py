from sysdi.utils import slugify


def test_slugify():
    assert slugify('Foo Bar Baz') == 'foo-bar-baz'
    assert slugify('Foo Bar ') == 'foo-bar'
    assert slugify('Foo: is - a Bar ') == 'foo-is-a-bar'
