from types import ModuleType, FunctionType
from dlai_grader.grading import test_case, object_to_grade
from dlai_grader.types import grading_function, grading_wrapper, learner_submission


def part_1(
    learner_mod: learner_submission,
    solution_mod: ModuleType | None = None,
) -> grading_function:
    @object_to_grade(learner_mod, "learner_func")
    def g(learner_func: FunctionType) -> list[test_case]:
        cases: list[test_case] = []

        t = test_case()
        if not isinstance(learner_func, FunctionType):
            t.fail()
            t.msg = "learner_func has incorrect type"
            t.want = FunctionType
            t.got = type(learner_func)
            return [t]

        return cases

    return g


def handle_part_id(part_id: str) -> grading_wrapper:
    grader_dict: dict[str, grading_wrapper] = {
        "123": part_1,
    }
    return grader_dict[part_id]
