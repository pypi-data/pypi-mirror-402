import re
from typing import Optional, Tuple, Union


class SemanticVersion:
    """
    Clase para manejar versionado semántico completo (MAJOR.MINOR.PATCH).
    Soporta pre-release y build metadata según semver 2.0.0.
    """

    VERSION_PATTERN = re.compile(
        r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
    )

    def __init__(self, version: Union[str, Tuple[int, int, int], 'SemanticVersion']):
        if isinstance(version, str):
            self.major, self.minor, self.patch, self.pre_release, self.build = self._parse_version(version)
        elif isinstance(version, tuple) and len(version) == 3:
            self.major, self.minor, self.patch = version
            self.pre_release = None
            self.build = None
        elif isinstance(version, SemanticVersion):
            self.major = version.major
            self.minor = version.minor
            self.patch = version.patch
            self.pre_release = version.pre_release
            self.build = version.build
        else:
            raise ValueError("Versión inválida. Debe ser string, tupla (major, minor, patch) o SemanticVersion.")

    def _parse_version(self, version_str: str) -> Tuple[int, int, int, Optional[str], Optional[str]]:
        match = self.VERSION_PATTERN.match(version_str)
        if not match:
            raise ValueError(f"Versión inválida: {version_str}")

        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        pre_release = match.group(4)
        build = match.group(5)

        return major, minor, patch, pre_release, build

    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            version += f"-{self.pre_release}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __repr__(self) -> str:
        return f"SemanticVersion('{self}')"

    def __eq__(self, other: 'SemanticVersion') -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch, self.pre_release, self.build) == \
               (other.major, other.minor, other.patch, other.pre_release, other.build)

    def __lt__(self, other: 'SemanticVersion') -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented

        # Comparar major, minor, patch
        self_tuple = (self.major, self.minor, self.patch)
        other_tuple = (other.major, other.minor, other.patch)

        if self_tuple != other_tuple:
            return self_tuple < other_tuple

        # Si son iguales, comparar pre-release
        if self.pre_release and other.pre_release:
            return self._compare_pre_release(self.pre_release, other.pre_release)
        elif self.pre_release:
            return True  # pre-release es menor que release
        elif other.pre_release:
            return False
        else:
            return False  # iguales

    def __le__(self, other: 'SemanticVersion') -> bool:
        return self < other or self == other

    def __gt__(self, other: 'SemanticVersion') -> bool:
        return not (self <= other)

    def __ge__(self, other: 'SemanticVersion') -> bool:
        return not (self < other)

    def _compare_pre_release(self, pre1: str, pre2: str) -> bool:
        """Compara identificadores de pre-release."""
        parts1 = pre1.split('.')
        parts2 = pre2.split('.')

        for p1, p2 in zip(parts1, parts2):
            if p1.isdigit() and p2.isdigit():
                if int(p1) != int(p2):
                    return int(p1) < int(p2)
            elif p1.isdigit():
                return True  # numérico < alfanumérico
            elif p2.isdigit():
                return False
            else:
                if p1 != p2:
                    return p1 < p2

        return len(parts1) < len(parts2)

    def increment_major(self) -> 'SemanticVersion':
        """Incrementa la versión major, resetea minor y patch."""
        return SemanticVersion((self.major + 1, 0, 0))

    def increment_minor(self) -> 'SemanticVersion':
        """Incrementa la versión minor, resetea patch."""
        return SemanticVersion((self.major, self.minor + 1, 0))

    def increment_patch(self) -> 'SemanticVersion':
        """Incrementa la versión patch."""
        return SemanticVersion((self.major, self.minor, self.patch + 1))

    def with_pre_release(self, pre_release: str) -> 'SemanticVersion':
        """Devuelve una nueva versión con pre-release."""
        new_version = SemanticVersion(self)
        new_version.pre_release = pre_release
        return new_version

    def with_build(self, build: str) -> 'SemanticVersion':
        """Devuelve una nueva versión con build metadata."""
        new_version = SemanticVersion(self)
        new_version.build = build
        return new_version

    @classmethod
    def parse(cls, version_str: str) -> 'SemanticVersion':
        """Parsea una string de versión."""
        return cls(version_str)

    @classmethod
    def from_tuple(cls, version_tuple: Tuple[int, int, int]) -> 'SemanticVersion':
        """Crea una versión desde una tupla."""
        return cls(version_tuple)