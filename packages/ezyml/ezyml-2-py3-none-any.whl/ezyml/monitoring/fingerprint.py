import hashlib, json

def dataset_fingerprint(df):
    payload = json.dumps(df.describe().to_dict(), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()

def compare_fingerprints(fp1, fp2):
    return fp1 == fp2
