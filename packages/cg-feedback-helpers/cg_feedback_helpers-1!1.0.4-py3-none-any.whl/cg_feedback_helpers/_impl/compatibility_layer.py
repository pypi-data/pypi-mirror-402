"""Compatibility layer for assertion functions developed in version 0.1
of the ``cg_feedback_helpers`` package. It uses :ref:`assertions.asserter`.
"""

from .assertions import asserter

# The following methods were the first API of the package. These
# are still used for some initial Pearson content in the Gaddis
# books.
assert_is_set = asserter.is_set
assert_equals = asserter.equals
assert_not_equals = asserter.not_equals
assert_is_of_type = asserter.is_of_type
assert_has_length = asserter.has_length
assert_not_none = asserter.not_none
assert_file_exists = asserter.file_exists
assert_is_imported = asserter.is_imported
emit_success = asserter.emit_success
