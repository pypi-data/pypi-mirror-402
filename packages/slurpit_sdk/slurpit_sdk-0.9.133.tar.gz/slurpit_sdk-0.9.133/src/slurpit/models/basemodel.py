

class BaseModel:
    def to_dict(self):
        return vars(self)

    def notify_unrecognized_fields(self, extra):
        import sys
        print(f"Unrecognized fields: {list(extra.keys())}")
        print("Please update your SDK to ensure compatibility. pip install --upgrade slurpit_sdk \n")
        sys.exit(1)
