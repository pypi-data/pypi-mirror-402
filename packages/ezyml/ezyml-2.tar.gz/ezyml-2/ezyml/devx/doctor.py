import sys

def doctor():
    issues=[]
    if sys.version_info < (3,9):
        issues.append("Python < 3.9 detected")
    return issues or ["Environment OK"]
