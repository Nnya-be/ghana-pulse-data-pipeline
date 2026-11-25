"""Python practice, day 1: lists and indexing (30 minutes).

How to work:
    1. Warm-up in the terminal (5 min)       -> see the list below
    2. Predictions (10 min)                  -> fill in PREDICTIONS, THEN run this file
    3. Three small functions (15 min)        -> replace each `raise NotImplementedError`
Run it with:  python python-practice/day01_lists.py

Rules: type everything yourself, predict before you run, never paste an answer.

Warm-up (type these in `python`, one at a time, and look at what comes back):
    nums = [10, 20, 30, 40, 50]
    len(nums)
    nums[0]
    nums[4]
    nums[5]            # what happens, and what is the error called?
"""

NUMS = [10, 20, 30, 40, 50]

# ---------------------------------------------------------------------------
# Part 2: predictions. Write what you think each expression gives, as a Python
# value (for example 30, or [10, 20]). Leave a line as None if you do not know,
# then look it up AFTER running the file.
# ---------------------------------------------------------------------------
PREDICTIONS = {
    "NUMS[1]": 20,
    "NUMS[-1]": 50,
    "NUMS[-2]": 40,
    "NUMS[1:3]": [20, 30],
    "NUMS[::2]": [10, 30, 50],
    "NUMS[::-1]":[50, 40, 30, 20, 10],
}


# ---------------------------------------------------------------------------
# Part 3: three functions.
# ---------------------------------------------------------------------------
def last_item(items):
    """Return the last item of the list. Return None for an empty list.

    last_item([1, 2, 3]) -> 3
    last_item([])        -> None
    """
    if not items:
        return None
    return items[-1]

def every_second(items):
    """Return the items at positions 0, 2, 4, ... as a NEW list.

    every_second([10, 20, 30, 40, 50]) -> [10, 30, 50]
    every_second([])                   -> []
    """
    return items[::2]


def reversed_copy(items):
    """Return a NEW list with the items in reverse order. The original must not change.

    reversed_copy([1, 2, 3]) -> [3, 2, 1]
    """
    return items[::-1]



def check_predictions():
    print("Part 2: predictions")
    right = 0
    for expression, guess in PREDICTIONS.items():
        actual = eval(expression, {"NUMS": NUMS})
        if guess is None:
            print(f"  {expression:<12} no prediction yet. Make one, then run again")
        elif guess == actual:
            print(f"  {expression:<12} right: {actual!r}")
            right += 1
        else:
            print(f"  {expression:<12} you said {guess!r}, it is {actual!r}")
    print(f"  {right} of {len(PREDICTIONS)} right\n")


def check_tasks():
    print("Part 3: functions")
    tests = {
        "last_item": [
            lambda: last_item([1, 2, 3]) == 3,
            lambda: last_item(["a"]) == "a",
            lambda: last_item([]) is None,
        ],
        "every_second": [
            lambda: every_second([10, 20, 30, 40, 50]) == [10, 30, 50],
            lambda: every_second([1, 2]) == [1],
            lambda: every_second([]) == [],
        ],
        "reversed_copy": [
            lambda: reversed_copy([1, 2, 3]) == [3, 2, 1],
            lambda: reversed_copy([]) == [],
            lambda: (lambda original: (reversed_copy(original), original)[1] == [1, 2, 3])([1, 2, 3]),
        ],
    }
    for name, checks in tests.items():
        passed = 0
        for check in checks:
            try:
                passed += 1 if check() else 0
            except NotImplementedError:
                break
            except Exception as error:  # a crash is a failed check, so say which one
                print(f"  {name}: crashed with {type(error).__name__}: {error}")
                break
        status = "PASS" if passed == len(checks) else "not yet"
        print(f"  {name:<14} {passed} of {len(checks)} checks   {status}")


if __name__ == "__main__":
    check_predictions()
    check_tasks()
