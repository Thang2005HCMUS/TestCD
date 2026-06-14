def pytest_addoption(parser):
    parser.addoption("--ns", action="store", default="default")