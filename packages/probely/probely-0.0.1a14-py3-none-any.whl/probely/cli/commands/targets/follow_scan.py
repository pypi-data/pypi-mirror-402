import logging
from time import time, sleep

from probely.cli.analytics.events import follow_scan_used_analytics_event
from probely.cli.common import (
    validate_and_retrieve_yaml_content,
)
from probely.cli.renderers import render_output
from probely.cli.tables.scan_table import ScanTable
from probely.exceptions import (
    ProbelyCLIError,
    ProbelyException,
)
from probely.sdk.enums import ScanStatusEnum, FindingSeverityEnum
from probely.sdk.helpers import build_scan_details_url
from probely.sdk.managers import TargetManager, ScanManager
from probely.settings import (
    CLI_POLLING_INTERVAL_SECS,
)

logger = logging.getLogger(__name__)


def cancel_followed_scan(scan, args):
    if args.continue_scan:
        args.console.print(f"Scan will continue: {build_scan_details_url(scan)}")
        return

    try:
        args.console.print("Canceling Scan...")
        ScanManager().cancel(scan)

    except ProbelyException as e:
        args.console.print("Failed to cancel scan")
        logger.debug("Failed to cancel scan: {}".format(e))


def check_scan_interrupted(scan_status: ScanStatusEnum, args):
    if scan_status not in ScanStatusEnum.interrupted_status():
        return

    if scan_status == ScanStatusEnum.PAUSED:
        args.console.print(
            f"Scan is {ScanStatusEnum.PAUSED.cli_choice}, meaning we don't know when it will continue. Command will fail"
        )

    raise ProbelyCLIError(f"Scan status is {scan_status.cli_choice}")


def check_timeout(start_time_secs, scan, args):
    if not args.timeout_mins:
        return

    current_time = time()
    timeout_secs = args.timeout_mins * 60
    scan_limit_time = start_time_secs + timeout_secs

    if current_time > scan_limit_time:
        args.console.print("Timeout reached...")

        cancel_followed_scan(scan, args)

        raise ProbelyCLIError("Command timeout")


def get_vulnerability_count(scan, args):
    if not args.severity_threshold:
        return scan.lows + scan.mediums + scan.highs + scan.criticals

    lower_bound_severity: FindingSeverityEnum = FindingSeverityEnum[
        args.severity_threshold
    ]
    severity_threshold = FindingSeverityEnum.get_severities_on_threshold(
        lower_bound_severity
    )

    threshold_vuln_count = 0
    if FindingSeverityEnum.LOW in severity_threshold:
        threshold_vuln_count += scan.lows
    if FindingSeverityEnum.MEDIUM in severity_threshold:
        threshold_vuln_count += scan.mediums
    if FindingSeverityEnum.HIGH in severity_threshold:
        threshold_vuln_count += scan.highs
    if FindingSeverityEnum.CRITICAL in severity_threshold:
        threshold_vuln_count += scan.criticals

    return threshold_vuln_count


def check_found_vulnerabilities(scan, args):
    vuln_count = get_vulnerability_count(scan, args)
    if vuln_count > 0:
        scan_url = build_scan_details_url(scan)

        if args.severity_threshold:
            raise ProbelyCLIError(
                f"scan found vulnerabilities within threshold: more details at {scan_url}"
            )

        raise ProbelyCLIError(f"scan found vulnerabilities: more details at {scan_url}")


def print_vulnerability_summary(scan, args):
    total_vuln_count = scan.lows + scan.mediums + scan.highs + scan.criticals
    args.console.print(
        f"Vulnerability summary: {total_vuln_count} Total | {scan.criticals} Criticals | {scan.highs} Highs | {scan.mediums} Mediums | {scan.lows} Lows"
    )


def should_fail_immediately(scan, args):
    if not args.fail_immediately:
        return False

    vuln_count = get_vulnerability_count(scan, args)

    if vuln_count > 0:
        args.console.print(
            "Found a vulnerability within command constrains, failing immediately"
        )
        cancel_followed_scan(scan, args)
        return True

    return False


def follow_scan(args, scan, start_time_secs):
    args.console.print(f"Scan's URL: {build_scan_details_url(scan)}")
    args.console.print("Following scan...")
    args.console.print(
        "Tip: Scan times vary significantly. Consider adjusting your scan-profile, running partial scans, or using the '--timeout' argument to limit this command run time."
    )

    scan_status = ScanStatusEnum.get_by_api_response_value(scan.status.value)
    last_status_reported = scan_status

    logger.debug("Starting loop checking scan stats....")

    while scan_status != ScanStatusEnum.COMPLETED:
        logger.debug("Retrieving Scan...")

        scan = ScanManager().retrieve(scan)
        scan_status = ScanStatusEnum.get_by_api_response_value(scan.status.value)

        check_timeout(start_time_secs, scan, args)

        if last_status_reported != scan_status:
            args.console.print("Scan Status updated to {}".format(scan_status.name))
            last_status_reported = scan_status
        else:
            logger.debug("No update on scan status....")

        check_scan_interrupted(scan_status, args)

        if should_fail_immediately(scan, args):
            break

        logger_msg = f"Scan hasn't finish. Waiting {str(CLI_POLLING_INTERVAL_SECS)} seconds until next check."
        logger.debug(logger_msg)

        sleep(CLI_POLLING_INTERVAL_SECS)


def targets_follow_scan_command_handler(args):
    target_id = args.target_id
    extra_payload = validate_and_retrieve_yaml_content(args.yaml_file_path)

    follow_scan_used_analytics_event(args, targets_count=1)

    start_time_secs = time()
    scan = TargetManager().start_scan(target_id, extra_payload)

    render_output(
        records=[scan],
        table_cls=ScanTable,
        args=args,
        is_single_record_output=True,
    )
    try:
        follow_scan(args, scan, start_time_secs)
    except KeyboardInterrupt:
        args.console.print("\nCommand was interrupted")
        cancel_followed_scan(scan, args)
        raise

    print_vulnerability_summary(scan, args)

    check_found_vulnerabilities(scan, args)
