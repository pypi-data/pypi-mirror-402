from fluidattacks_core.semver.match_versions import (
    _simplify_pre_release,
    compare_pre_releases,
    compare_versions,
    match_vulnerable_versions,
    normalize,
)
from pydantic import BaseModel

from labels.model.advisories import (
    Advisory,
    AdvisoryFixMetadata,
    AdvisoryFixMetadataNew,
    FixMetadata,
    ResidualCVES,
    SeverityCVES,
    UpgradeType,
)

COMMON_QUALIFIERS = {
    "RELEASE",
    "Final",
    "GA",
    "GA.RELEASE",
    "RELEASE.FINAL",
    "FINAL",
    "STABLE",
    "LTS",
    "GA.FINAL",
}


class VersionMetadata(BaseModel):
    pre: str | None
    qual: str | None
    build: str | None


def _is_qualifier(part: str) -> bool:
    return part.upper() in {q.upper() for q in COMMON_QUALIFIERS}


def _extract_build_metadata(parts: list[str]) -> tuple[list[str], str | None]:
    clean_parts = []
    build_metadata = None

    for part in parts:
        if "+" in part:
            num_part, build_part = part.split("+", 1)
            clean_parts.append(num_part)
            build_metadata = build_part
        else:
            clean_parts.append(part)

    return clean_parts, build_metadata


def _extract_qualifier(parts: list[str]) -> tuple[list[str], str | None]:
    for index_part in range(1, len(parts)):
        if _is_qualifier(parts[index_part]):
            return parts[:index_part] + parts[index_part + 1 :], parts[index_part]
    return parts, None


def _normalize_version_for_comparison(
    version: str,
) -> tuple[list[str], str | None, str | None, str | None]:
    parts, pre_release = normalize(version)

    clean_parts, build_metadata = _extract_build_metadata(parts)
    final_parts, qualifier = _extract_qualifier(clean_parts)

    simplified_pre_release = None
    if pre_release:
        simplified_pre_release = _simplify_pre_release(pre_release.lower())

    return final_parts, simplified_pre_release, qualifier, build_metadata


def _are_versions_equivalent(version1: str, version2: str) -> bool:
    v1_parts, v1_pre, _, _ = _normalize_version_for_comparison(version1)
    v2_parts, v2_pre, _, _ = _normalize_version_for_comparison(version2)
    return v1_parts == v2_parts and v1_pre == v2_pre


def _is_build_metadata_greater(v_build: str | None, dep_build: str | None) -> bool | None:
    if v_build is None and dep_build is not None:
        return True
    if v_build is not None and dep_build is None:
        return False
    if v_build is not None and dep_build is not None:
        return v_build > dep_build
    return None


def _compare_single_part(v_part: str, dep_part: str) -> bool | None:
    if v_part.isdigit() and dep_part.isdigit():
        v_num = int(v_part)
        dep_num = int(dep_part)
        return v_num > dep_num if v_num != dep_num else None
    return v_part > dep_part if v_part != dep_part else None


def _compare_common_parts(v_parts: list[str], dep_parts: list[str]) -> bool | None:
    min_parts = min(len(v_parts), len(dep_parts))

    for index_part in range(min_parts):
        comparison = _compare_single_part(v_parts[index_part], dep_parts[index_part])
        if comparison is not None:
            return comparison

    return None


def _is_version_greater_than_dep(version: str, dep_version: str) -> bool:
    if not version or not dep_version or "${" in version or "${" in dep_version:
        return False

    if _are_versions_equivalent(version, dep_version):
        return False

    if compare_versions(version1=version, version2=dep_version, include_same=False):
        return True

    dep_parts, dep_pre, _, dep_build = _normalize_version_for_comparison(dep_version)
    v_parts, v_pre, _, v_build = _normalize_version_for_comparison(version)

    result = None

    if v_parts == dep_parts and v_pre is None and dep_pre is not None:
        result = True
    elif v_parts == dep_parts and v_pre is not None and dep_pre is not None:
        result = compare_pre_releases(v_pre, dep_pre)
    elif v_parts == dep_parts:
        build_comparison = _is_build_metadata_greater(v_build, dep_build)
        if build_comparison is not None:
            result = build_comparison

    if result is not None:
        return result

    common_parts_comparison = _compare_common_parts(v_parts, dep_parts)
    if common_parts_comparison is not None:
        return common_parts_comparison

    return len(v_parts) > len(dep_parts)


def _get_upgrade_type_from_numeric_parts(
    cur_nums: list[int], tgt_nums: list[int]
) -> UpgradeType | None:
    if tgt_nums[0] > cur_nums[0]:
        return UpgradeType.MAJOR
    if tgt_nums[1] > cur_nums[1]:
        return UpgradeType.MINOR
    if tgt_nums[2] > cur_nums[2]:
        return UpgradeType.PATCH
    return None


def _get_upgrade_type_from_metadata(
    cur_meta: VersionMetadata, tgt_meta: VersionMetadata
) -> UpgradeType:
    if tgt_meta.pre and cur_meta.pre != tgt_meta.pre:
        return UpgradeType.PATCH
    if tgt_meta.pre is None and cur_meta.pre is not None:
        return UpgradeType.PATCH
    if cur_meta.qual != tgt_meta.qual or cur_meta.build != tgt_meta.build:
        return UpgradeType.PATCH
    return UpgradeType.UNKNOWN


def _get_upgrade_type_from_index(part_index: int) -> UpgradeType:
    if part_index == 0:
        return UpgradeType.MAJOR
    if part_index == 1:
        return UpgradeType.MINOR
    return UpgradeType.PATCH


def _get_upgrade_type_from_parts(cur_parts: list[str], tgt_parts: list[str]) -> UpgradeType | None:
    min_parts = min(len(cur_parts), len(tgt_parts))

    for part_index in range(min_parts):
        if cur_parts[part_index] == tgt_parts[part_index]:
            continue

        if cur_parts[part_index].isdigit() and tgt_parts[part_index].isdigit():
            cur_num = int(cur_parts[part_index])
            tgt_num = int(tgt_parts[part_index])
            if cur_num != tgt_num:
                return _get_upgrade_type_from_index(part_index)

        return UpgradeType.PATCH

    return UpgradeType.PATCH if len(cur_parts) != len(tgt_parts) else None


def get_upgrade_type(current: str, target: str) -> UpgradeType:
    cur_parts, cur_pre, cur_qual, cur_build = _normalize_version_for_comparison(current)
    tgt_parts, tgt_pre, tgt_qual, tgt_build = _normalize_version_for_comparison(target)

    cur_nums = [int(p) if p.isdigit() else 0 for p in ([*cur_parts, "0", "0", "0"])[:3]]
    tgt_nums = [int(p) if p.isdigit() else 0 for p in ([*tgt_parts, "0", "0", "0"])[:3]]

    numeric_upgrade = _get_upgrade_type_from_numeric_parts(cur_nums, tgt_nums)
    if numeric_upgrade:
        return numeric_upgrade

    part_upgrade = _get_upgrade_type_from_parts(cur_parts, tgt_parts)
    if part_upgrade:
        return part_upgrade

    cur_meta = VersionMetadata(pre=cur_pre, qual=cur_qual, build=cur_build)
    tgt_meta = VersionMetadata(pre=tgt_pre, qual=tgt_qual, build=tgt_build)
    return _get_upgrade_type_from_metadata(cur_meta, tgt_meta)


def version_sort_key(version: str) -> tuple:
    parts, pre, _, _ = _normalize_version_for_comparison(version)
    nums = tuple(int(p) if p.isdigit() else 0 for p in ([*parts, "0", "0", "0"])[:3])
    is_release = 1 if pre is None else 0
    pre_str = pre or ""
    return (*nums, is_release, pre_str)


def match_fixed_versions(
    dep_version: str, advisory: Advisory, safe_versions: list[str] | None
) -> Advisory:
    cve_fix_versions = advisory.fixed_versions or safe_versions
    closest_fix = None
    upgrade_type = UpgradeType.UNKNOWN
    breaking_change = False

    if cve_fix_versions:
        fixed = [v for v in cve_fix_versions if _is_version_greater_than_dep(v, dep_version)]
        if fixed:
            closest_fix = min(fixed, key=version_sort_key)
            upgrade_type = get_upgrade_type(dep_version, closest_fix)
            breaking_change = upgrade_type == UpgradeType.MAJOR

    closest_safe = None
    if safe_versions:
        safe = [v for v in safe_versions if _is_version_greater_than_dep(v, dep_version)]
        if safe:
            closest_safe = min(safe, key=version_sort_key)

    if not closest_fix and not closest_safe:
        advisory.fix_metadata = None
        return advisory

    if not closest_fix and closest_safe:
        closest_fix = closest_safe
        upgrade_type = get_upgrade_type(dep_version, closest_fix)
        breaking_change = upgrade_type == UpgradeType.MAJOR

    if closest_fix is None:
        advisory.fix_metadata = None
        return advisory

    advisory.fix_metadata = AdvisoryFixMetadata(
        closest_fix_version=closest_fix,
        upgrade_type=upgrade_type,
        breaking_change=breaking_change,
        closest_safe_version=closest_safe,
    )

    return advisory


def _create_severity_cves(advisories: list[Advisory]) -> SeverityCVES | None:
    total = len(advisories)
    if total == 0:
        return None
    critical = []
    high = []
    medium = []
    low = []

    for advisory in advisories:
        severity_lower = advisory.severity_level.lower() if advisory.severity_level else "low"
        if severity_lower == "critical":
            critical.append(advisory.id)
        elif severity_lower == "high":
            high.append(advisory.id)
        elif severity_lower == "medium":
            medium.append(advisory.id)
        elif severity_lower == "low":
            low.append(advisory.id)

    return SeverityCVES(
        critical=critical if critical else None,
        high=high if high else None,
        medium=medium if medium else None,
        low=low if low else None,
        total=len(advisories),
    )


def _advisory_key(advisory: Advisory) -> tuple[str, str]:
    """Generate a hashable key for an advisory for fast set operations."""
    return (advisory.id, advisory.vulnerable_version)


def _get_residual_cves(
    candidate_fix_version: str, dep_version: str, all_package_advisories: list[Advisory]
) -> ResidualCVES | None:
    base_advisories = [
        a
        for a in all_package_advisories
        if match_vulnerable_versions(dep_version, a.vulnerable_version)
    ]

    candidate_advisories = [
        advisory
        for advisory in all_package_advisories
        if match_vulnerable_versions(candidate_fix_version, advisory.vulnerable_version)
    ]

    base_keys = {_advisory_key(a) for a in base_advisories}
    candidate_keys = {_advisory_key(a) for a in candidate_advisories}

    remedied_cves = [a for a in base_advisories if _advisory_key(a) not in candidate_keys]
    maintained_cves = [a for a in candidate_advisories if _advisory_key(a) in base_keys]
    introduced_cves = [a for a in candidate_advisories if _advisory_key(a) not in base_keys]

    remedied = _create_severity_cves(remedied_cves)
    maintained = _create_severity_cves(maintained_cves)
    introduced = _create_severity_cves(introduced_cves)

    if remedied is None and maintained is None and introduced is None:
        return None

    return ResidualCVES(
        remedied=remedied,
        maintained=maintained,
        introduced=introduced,
    )


def _calculate_minimal_fix(
    dep_version: str,
    advisories: list[Advisory],
    cve_fix_versions: list[str] | None,
) -> FixMetadata | None:
    if cve_fix_versions:
        fixed = [v for v in cve_fix_versions if _is_version_greater_than_dep(v, dep_version)]
        if fixed:
            closest_min_fix = min(fixed, key=version_sort_key)
            min_upgrade_type = get_upgrade_type(dep_version, closest_min_fix)
            min_residual_cves = _get_residual_cves(closest_min_fix, dep_version, advisories)
            return FixMetadata(
                fix_version=closest_min_fix,
                upgrade_type=min_upgrade_type,
                breaking_change=min_upgrade_type == UpgradeType.MAJOR,
                residual_cves=min_residual_cves,
            )

    return None


def _calculate_complete_fix(
    dep_version: str,
    advisories: list[Advisory],
    complete_fix_versions: list[str] | None,
) -> FixMetadata | None:
    if complete_fix_versions:
        complete_fix_list = [
            v for v in complete_fix_versions if _is_version_greater_than_dep(v, dep_version)
        ]
        if complete_fix_list:
            closest_complete_fix = min(complete_fix_list, key=version_sort_key)
            complete_upgrade_type = get_upgrade_type(dep_version, closest_complete_fix)
            complete_residual_cves = _get_residual_cves(
                closest_complete_fix, dep_version, advisories
            )
            return FixMetadata(
                fix_version=closest_complete_fix,
                upgrade_type=complete_upgrade_type,
                breaking_change=complete_upgrade_type == UpgradeType.MAJOR,
                residual_cves=complete_residual_cves,
            )
    return None


def _calculate_safe_fix(  # noqa: PLR0913
    dep_version: str,
    minimal_fix: FixMetadata,
    complete_fix: FixMetadata,
    all_package_versions: list[str],
    advisories: list[Advisory],
    advisory: Advisory,
) -> FixMetadata | None:
    minimal_fix_version = minimal_fix.fix_version
    complete_fix_version = complete_fix.fix_version
    safe_version_candidates = [
        v
        for v in all_package_versions
        if _is_version_greater_than_dep(v, minimal_fix_version)
        and _is_version_greater_than_dep(complete_fix_version, v)
    ]
    if safe_version_candidates:
        valid_safe_candidates = {}
        for candidate in safe_version_candidates:
            if match_vulnerable_versions(candidate, advisory.vulnerable_version):
                continue

            residual_cves = _get_residual_cves(candidate, dep_version, advisories)
            if (
                residual_cves is not None
                and residual_cves.introduced is not None
                and residual_cves.introduced.total > 0
            ):
                continue

            valid_safe_candidates[candidate] = residual_cves

        if valid_safe_candidates:
            closest_safe_version = min(valid_safe_candidates.keys(), key=version_sort_key)
            residual_cves = valid_safe_candidates[closest_safe_version]
            safe_upgrade_type = get_upgrade_type(dep_version, closest_safe_version)
            return FixMetadata(
                fix_version=closest_safe_version,
                upgrade_type=safe_upgrade_type,
                breaking_change=safe_upgrade_type == UpgradeType.MAJOR,
                residual_cves=residual_cves,
            )
    return None


def match_fixed_versions_new(
    dep_version: str,
    advisory: Advisory,
    complete_fix_versions: list[str] | None,
    all_package_versions: list[str],
    advisories: list[Advisory],
) -> Advisory:
    cve_fix_versions = advisory.fixed_versions

    minimal_fix = _calculate_minimal_fix(dep_version, advisories, cve_fix_versions)
    complete_fix = _calculate_complete_fix(dep_version, advisories, complete_fix_versions)

    if not minimal_fix and complete_fix:
        minimal_fix = complete_fix

    safe_fix = None
    if minimal_fix:
        residual = minimal_fix.residual_cves
        has_no_introduced = (
            residual is None or residual.introduced is None or residual.introduced.total == 0
        )
        if has_no_introduced:
            safe_fix = minimal_fix

    if minimal_fix and complete_fix and not safe_fix:
        safe_fix = _calculate_safe_fix(
            dep_version, minimal_fix, complete_fix, all_package_versions, advisories, advisory
        )
    if not minimal_fix and not complete_fix and not safe_fix:
        advisory.fix_metadata_new = None
        return advisory

    if minimal_fix is None:
        advisory.fix_metadata_new = None
        return advisory

    advisory.fix_metadata_new = AdvisoryFixMetadataNew(
        closest_min_fix=minimal_fix,
        closest_complete_fix=complete_fix,
        closest_safe_fix=safe_fix,
    )

    return advisory


def match_fixes(
    dep_version: str,
    advisory: Advisory,
    complete_fix_versions: list[str] | None,
    all_package_versions: list[str],
    advisories: list[Advisory],
) -> Advisory:
    match_fixed_versions(dep_version, advisory, complete_fix_versions)
    match_fixed_versions_new(
        dep_version, advisory, complete_fix_versions, all_package_versions, advisories
    )
    return advisory
