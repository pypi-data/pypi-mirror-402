from collections.abc import Callable
from types import ModuleType

from .grading import LearnerSubmission, test_case

grading_function = Callable[..., list[test_case]]
learner_submission = ModuleType | LearnerSubmission
grading_wrapper = Callable[[learner_submission, ModuleType | None], grading_function]
