from waiba_hello import hello

def test_say_hello():
    assert hello() == "Hello from Waiba!"


if __name__ == "__main__":
    test_say_hello()