# cg_feedback_helpers

This package provides functionality to provide feedback messages. It
mainly provides the class `Asserter`. The `Asserter` has a number of
methods that are documented on [the official
docs](http://feedback-helpers.atv2.codegrade.com/index.html), which allow 
to run assertions. Each assertion can provide either positive or negative
feedback. A few helpers are also provided to aid with input and output
coupled when running assertions. At the end of a run, call
`Asserter::emit_success` to guarantee the user receives some feedback
if everything was correct.

The package outputs feedback in the following format:

```json
{
    "tag": "feedback",
    "contents": [
        {
            "value": <your feedback message>,
            "sentiment": <"positive" | "negative">
        },
    ]
}
```

## Usage:

The following example shows how the asserter can be used to check that
the function `greet_user` responds with the correct output to a user
input.

```py
from cg_feedback_helpers import asserter, helpers

def greet_user():
    name = input()
    print(f"Hi {name}")


with helpers.capture_output() as buffer, helpers.as_stdin("John"):
    greet_user()

output = helpers.get_lines_from_buffer(buffer)
asserter.has_length(output, 1)
asserter.equals(output[0], "John")
asserter.emit_success()
```

The output of which will be:

```
{"tag":"feedback","contents":[{"value":"Got expected length 1","sentiment":"positive"}]}
{"tag":"feedback","contents":[{"value":"Got expected value Hi John","sentiment":"positive"}]}
{"tag":"feedback","contents":[{"value":"Everything was correct! Good job!","sentiment":"positive"}]}
```

## Module contains:

- `Asserter` class, of which the default messages produced can be
  configured, as well as its failure behavior (either using exceptions
  or `sys.exit`);
- `helpers` to make it easier to work with input/output tests.

# Limitation:

The module currently does not support markdown feedback, nor the
`neutral` sentiment.
