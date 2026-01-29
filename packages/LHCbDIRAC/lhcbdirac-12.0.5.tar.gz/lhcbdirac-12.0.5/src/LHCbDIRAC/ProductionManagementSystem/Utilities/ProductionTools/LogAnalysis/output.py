###############################################################################
# (c) Copyright 2024 CERN for the benefit of the LHCb Collaboration           #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
from __future__ import annotations

__all__ = [
    "to_markdown",
]

from operator import itemgetter

from .prod_analyzer import GroupedProblems, AggregatedLFNDebugInfo
from .base_reasons import LogFileMatch


def _nop_grouper(
    instances: list[AggregatedLFNDebugInfo],
) -> list[tuple[str | None, str | None, list[AggregatedLFNDebugInfo]]]:
    return [(None, None, instances)]


def human_readable_size(size: int) -> str:
    for unit in ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} YiB"


def to_markdown(
    grouped_problems: GroupedProblems, *, is_summary: bool, instance_grouper=_nop_grouper, title: str | None = None
):
    n_lfns = len({(z.transform_id, z.lfn) for x in grouped_problems.values() for y in x.values() for z in y})

    if title is None:
        title = f"Summary of {n_lfns} files"
    body = [f"# {title}\n"]
    for reason_type, matches in sorted(grouped_problems.items()):
        if reason_type:
            body.append(f"## {reason_type}\n")
        for n, (match, instances) in enumerate(sorted(matches.items()), start=1):
            n_reason_lfns = len({(x.lfn, x.transform_id) for x in instances})
            if reason_type == "":
                body.append(f"### {match} in {n_reason_lfns} LFNs\n")
            else:
                if len(matches) > 1:
                    body.append(f"### {reason_type} ({n}) in {n_reason_lfns} LFNs\n")
                body.append(f"```\n{match}\n```\n")
                if reason_type == "KnownCorruptedFile":
                    body.append(
                        "This file is known to contain some corrupt events. It "
                        "likely cannot be recovered for this production however "
                        "we typically don't delete these files as other analyses "
                        "might not depend on the bad branches.\n"
                    )
                else:
                    reason_class = LogFileMatch.name_to_reason[reason_type]  # pylint: disable=unsubscriptable-object
                    if reason_class.explanation:
                        body.append(reason_class.explanation + "\n")
                    if hasattr(reason_class, "issue_url"):
                        body.append(f"See {reason_class.issue_url}.\n")

            for key, key_info, grouped_instances in instance_grouper(instances):
                if key is not None:
                    body.append(f"#### {key}\n")
                if key_info is not None:
                    body.append(f"{key_info}\n")
                body.extend(make_problems_table(grouped_instances, is_summary=is_summary))

    return "\n".join(body)


def make_problems_table(
    grouped_instances: list[AggregatedLFNDebugInfo],
    *,
    is_summary: bool,
    transform_to_group: dict[int, str] | None = None,
) -> list[str]:
    table = [
        "| Transform | LFN | Job ID | Site | Peak Mem | Log URL(s) |",
        "| --------- | --- | ------ | ---- | -------- | ---------- |",
    ]
    if transform_to_group:
        table[0] = "| Group " + table[0]
        table[1] = "| ----- " + table[1]
    if is_summary:
        table[0] += " Occurrences |"
        table[1] += " ----------- |"
    prev_lfn = None
    prev_transform_id = None
    for instance in sorted(grouped_instances, key=lambda x: (x.transform_id, x.lfn, x.job_id)):
        transform_id = ""
        lfn = ""
        if prev_transform_id != instance.transform_id:
            prev_transform_id = instance.transform_id
            transform_id = f"`{instance.transform_id}`"
            lfn = f"`{instance.lfn}`"
        elif prev_lfn != instance.lfn:
            lfn = f"`{instance.lfn}`"
        prev_lfn = instance.lfn
        log_urls = sorted(instance.log_urls, reverse=True)[:3] if is_summary else [instance.log_url]
        if is_summary:
            sites = " ".join(
                f"{f'**{k}**' if k == instance.site else k} ({v})"
                for k, v in sorted(instance.sites.items(), key=itemgetter(1), reverse=True)
            )
        else:
            sites = instance.site

        line = [
            transform_id,
            lfn,
            instance.job_id,
            sites,
            human_readable_size(instance.peak_memory) if instance.peak_memory else "",
            " ".join(f"[here]({url})" for url in log_urls if url),
        ]
        if transform_to_group:
            line.insert(0, transform_to_group[instance.transform_id])
        if is_summary:
            line.append(f"{instance.occurrences} / {instance.attempts}")
        table.append("| " + " | ".join(map(str, line)) + " |")

    table.append("")
    return table
