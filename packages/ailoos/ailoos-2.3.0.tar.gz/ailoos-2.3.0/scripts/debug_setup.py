from setuptools import find_packages

packages = find_packages(where="src", exclude=[
    "ailoos.coordinator*", 
    "ailoos.infrastructure*",
    "ailoos.zero_trust*",
    "ailoos.active_learning*",
    "ailoos.blue_green_deployment*",
    "ailoos.security*",
])
print("Found packages:", packages)

import os
if os.path.isdir("src/ailoos"):
    print("src/ailoos exists")
else:
    print("src/ailoos DOES NOT exist")
