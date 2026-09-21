import pickle


def load_job(user_data):
    # VULNERABLE: DRISHTI-DESER-019 / CWE-502
    return pickle.loads(user_data)

# Expected fix: use a safe, constrained serialization format.
