from setuptools import setup

setup(
    name="pymidisoundboard",
    version="0.0.1",
    author="travis mick",
    author_email="root@lo.calho.st",
    description="gstreamer-based application that lets you use a midi controller as a soundboard",
    packages=['pymidisoundboard'],
    python_requires='>=3.8',
    install_requires=['PyGObject>=3.40,<4.0', 'mido>=1.2,<2', 'python-rtmidi>=1.4,<2', 'PyQt5>=5.15,<6', 'pyyaml>=5.4,<6'],
    entry_points={'console_scripts': ["pymidisoundboard=pymidisoundboard.main:main"]}
)
