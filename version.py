class Version:
    main_version = 0
    secondary_version = 0
    def __init__(self, str_version:str):
        version_code = str_version.split(".")
        self.main_version = int(version_code[1]) if len(version_code) > 1 else 0
        self.secondary_version = int(version_code[2]) if len(version_code) > 2 else 0

    def __str__(self):
        return f"1.{self.main_version}.{self.secondary_version}"

    def __repr__(self):
        return f"Version(str_version='{self.__str__()}')"

    def __eq__(self, other):
        return self.main_version == other.main_version and self.secondary_version == other.secondary_version
    def __gt__(self, other):
        return self.main_version > other.main_version or (self.main_version == other.main_version and self.secondary_version > other.secondary_version)
    def __lt__(self, other):
        return self.main_version < other.main_version or (self.main_version == other.main_version and self.secondary_version < other.secondary_version)
    def __ge__(self, other):
        return self.main_version >= other.main_version or (self.main_version == other.main_version and self.secondary_version >= other.secondary_version)
    def __le__(self, other):
        return self.main_version <= other.main_version or (self.main_version == other.main_version and self.secondary_version <= other.secondary_version)
    def __ne__(self, other):
        return self.main_version != other.main_version or self.secondary_version != other.secondary_version