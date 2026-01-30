# loggez: Python EZ logging

Control logging levels with env vars and have a unique logger per name, for fine-tuned control over logging in various subsystems of your application.
By default it only writes to stderr. Optional support for logging to a file too.

## Installation

```
pip install loggez
```

## Usage:
```python
# run.py
from loggez import make_logger, loggez_logger
from loguru import logger # compatibility with other logging systems

logger.info("loguru hi")
my_logger = make_logger("my_logger") # make a new logger with the unique key 'my_logger' for env variables
my_logger.info("my_logger hi") # shows by default, can be turned off with running via my_logger_LOGLEVEL=0 app.py
my_logger.debug("my_logger hi") # shows only if you run with my_logger_LOGLEVEL=2 app.py (or higher)
my_logger.trace("my_logger hi") # LOGLEVEL >= 3
my_logger.trace2("my_logger hi") # LOGLEVEL >= 4

my_logger2 = make_logger("my_logger2", log_file=Path.cwd()/"log.txt") # optional file logging too
my_logger2.info("my_logger2 hi")
my_logger2.debug("my_logger2 hi")
my_logger2.trace("my_logger2 hi")
my_logger2.trace2("my_logger hi")

loggez_logger.info("loggez_logger hi") # the default logger object
loggez_logger.debug("loggez_logger hi")
loggez_logger.trace("loggez_logger hi")
loggez_logger.trace2("loggez_logger hi")

```

Run with:
```
my_logger_LOGLEVEL=0 run.py # no message
my_logger_LOGLEVEL=1 run.py # for info (defualt)
my_logger_LOGLEVEL=2 run.py # for debug
LOGGEZ_LOGLEVEL=3 run.py # for trace
```

Additional env vars:
- `my_logger_MESSAGE=...`: see the default in `loggez/loggez.py` to control colors and stuff.
- `my_logger_INFO_MESSAGE=...`, `my_logger_DEBUG_MESSAGE=...` etc.

Note: You can use also use the global predefined logger: `from loggez import loggez_logger as logger; logger.info(...)`.
Env variables are: `LOGGEZ_LOGLEVEL=...`, `LOGGEZ_INFO_MESSAGE=....` etc.

That's all.
