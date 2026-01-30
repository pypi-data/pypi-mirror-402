from enum import Enum

from pydantic import BaseModel

AdvisoryRecord = tuple[
    str,  # id
    str,  # source
    str,  # vulnerable_version
    str | None,  # severity_level
    str | None,  # severity_v4
    str | None,  # epss
    str | None,  # details
    str | None,  # percentile
    str | None,  # cwe_ids
    str | None,  # cve_finding
    int,  # auto_approve
    str | None,  # fixed_versions,
    int,  # kev_catalog
    str | None,  # platform_version
]


class UpgradeType(str, Enum):
    UNKNOWN = "unknown"
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class SeverityCVES(BaseModel):
    critical: list[str] | None = None
    high: list[str] | None = None
    medium: list[str] | None = None
    low: list[str] | None = None
    total: int


class ResidualCVES(BaseModel):
    remedied: SeverityCVES | None = None
    maintained: SeverityCVES | None = None
    introduced: SeverityCVES | None = None


class FixMetadata(BaseModel):
    fix_version: str
    upgrade_type: UpgradeType
    breaking_change: bool
    residual_cves: ResidualCVES | None = None


class AdvisoryFixMetadataNew(BaseModel):
    closest_min_fix: FixMetadata
    closest_safe_fix: FixMetadata | None = None
    closest_complete_fix: FixMetadata | None = None


class AdvisoryFixMetadata(BaseModel):
    closest_fix_version: str
    upgrade_type: UpgradeType
    breaking_change: bool
    closest_safe_version: str | None = None


class Advisory(BaseModel):
    id: str
    vulnerable_version: str
    source: str
    package_manager: str
    cpes: list[str]
    severity_level: str = "Low"
    platform_version: str | None = None
    fixed_versions: list[str] | None = None
    fix_metadata: AdvisoryFixMetadata | None = None
    fix_metadata_new: AdvisoryFixMetadataNew | None = None
    details: str | None = None
    epss: float = 0.0
    percentile: float = 0.0
    severity_v4: str | None = None
    cwe_ids: list[str] | None = None
    cve_finding: str | None = None
    auto_approve: bool = False
    upstream_package: str | None = None
    kev_catalog: bool = False
