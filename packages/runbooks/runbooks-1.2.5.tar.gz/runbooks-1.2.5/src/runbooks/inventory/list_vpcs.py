#!/usr/bin/env python3
"""
AWS VPC Inventory Collection

A comprehensive VPC discovery tool for multi-account AWS Organizations that provides
detailed network topology visibility across all accounts and regions. Supports
filtering for default VPCs to identify potential security risks.

**AWS API Mapping**: `boto3.client('ec2').describe_vpcs()`

.. TODO v1.1.11: Performance optimization for large-scale VPC discovery
   - Current: Timeouts at 540s for AWS Organizations with 100+ accounts
   - Root Cause: Threading pool size (max 25) insufficient for large-scale discovery
   - Improvement: Dynamic ThreadPoolExecutor sizing + concurrent pagination
   - Target: Complete VPC discovery in <120s for 100+ accounts across 16 regions
   - Reference: FinOps proven pattern (optimal_workers = min(accounts * regions, 50))

Features:
    - Multi-account VPC discovery via AWS Organizations
    - Default VPC identification for security auditing
    - CIDR block and association analysis
    - VPC peering and gateway information
    - Tag-based metadata collection
    - Cross-region network topology mapping

Compatibility:
    - AWS Organizations with cross-account roles
    - AWS Control Tower managed accounts
    - Standalone AWS accounts
    - All AWS regions including opt-in regions

Example:
    Discover all VPCs across organization:
    ```bash
    python ec2_describe_vpcs.py --profile my-org-profile
    ```
    
    Find only default VPCs for security audit:
    ```bash
    python ec2_describe_vpcs.py --profile my-profile --default
    ```
    
    Export VPC inventory to file:
    ```bash
    python ec2_describe_vpcs.py --profile my-profile \\
        --save vpc_inventory.json --output json
    ```

Requirements:
    - IAM permissions: `ec2:DescribeVpcs`, `sts:AssumeRole`
    - AWS Organizations access (for multi-account scanning)
    - Python 3.8+ with required dependencies

Author:
    AWS Cloud Foundations Team
    
Version:
    2024.01.26
"""

import logging
import sys
from queue import Queue
import ipaddress
from typing import List, Dict, Tuple
import pandas as pd

# from tqdm.auto import tqdm
from threading import Thread
from time import time

from runbooks.inventory import inventory_modules as Inventory_Modules
from runbooks.inventory.ArgumentsClass import CommonArguments
from botocore.exceptions import ClientError
from runbooks.inventory.inventory_modules import display_results, get_all_credentials
from runbooks.common.rich_utils import console
from runbooks import __version__


# Terminal control constants
ERASE_LINE = "\x1b[2K"


##########################
# CIDR Conflict Detection (Track 5: v1.1.19)
##########################


class CIDRConflictDetector:
    """
    Detect CIDR overlaps across multi-account VPCs for VPC recreation safety (JIRA AWSO-65).

    Business Context:
        - VPC CIDR overlaps prevent VPC peering and Transit Gateway attachments
        - Critical for multi-account network architecture planning
        - Enables safe VPC recreation by identifying CIDR conflicts before changes

    Use Cases:
        - Pre-migration CIDR validation (prevent overlapping networks)
        - VPC peering feasibility assessment
        - Transit Gateway attachment planning
        - Network architecture compliance auditing

    Implementation (Track 5: Inventory VPC Enhancement):
        - Organization-wide VPC discovery with CIDR extraction
        - N×N CIDR overlap detection using ipaddress.ip_network.overlaps()
        - Severity classification (HIGH: prevents peering/TGW)
        - Excel export for business stakeholders

    Example:
        # Discover VPCs across organization
        vpcs = [
            {'vpc_id': 'vpc-111', 'account_id': '111122223333', 'cidr_block': '10.0.0.0/16'},
            {'vpc_id': 'vpc-222', 'account_id': '444455556666', 'cidr_block': '10.0.128.0/17'}
        ]

        # Detect conflicts
        detector = CIDRConflictDetector(vpcs)
        conflicts = detector.detect_overlaps()

        # Export to Excel for stakeholder review
        detector.export_conflicts('/tmp/vpc-cidr-conflicts.xlsx')

    JIRA Integration:
        AWSO-65: 3 VPCs requiring CIDR recreation
        - This detector validates no overlaps exist before VPC recreation
        - Prevents network architecture violations during migration
    """

    def __init__(self, vpcs: List[Dict]):
        """
        Initialize CIDR conflict detector with VPC inventory.

        Args:
            vpcs: List of VPC dictionaries containing:
                - vpc_id: AWS VPC identifier
                - account_id: AWS account ID
                - cidr_block: VPC CIDR block (e.g., '10.0.0.0/16')
                - region: AWS region
                - vpc_name: VPC name from tags (optional)
        """
        self.vpcs = vpcs
        self.conflicts = []

    def detect_overlaps(self) -> List[Dict]:
        """
        Detect CIDR overlaps between VPCs using N×N comparison.

        Algorithm:
            - Nested loop comparing each VPC pair
            - ipaddress.ip_network.overlaps() for overlap detection
            - Handles IPv4 and IPv6 CIDR blocks
            - Self-comparison excluded (i < j iteration)

        Returns:
            List of conflict dictionaries containing:
                - vpc1: First VPC ID
                - vpc1_account: First VPC account ID
                - vpc1_cidr: First VPC CIDR block
                - vpc2: Second VPC ID
                - vpc2_account: Second VPC account ID
                - vpc2_cidr: Second VPC CIDR block
                - severity: 'HIGH' (prevents peering/TGW)

        Network Impact:
            - HIGH severity = Cannot establish VPC peering
            - HIGH severity = Cannot attach to Transit Gateway
            - HIGH severity = VPN/Direct Connect routing conflicts
        """
        logging.info(f"Starting CIDR conflict detection across {len(self.vpcs)} VPCs")

        for i, vpc1 in enumerate(self.vpcs):
            for vpc2 in self.vpcs[i + 1 :]:  # Avoid duplicate comparisons
                try:
                    if self._check_cidr_overlap(vpc1["CIDR"], vpc2["CIDR"]):
                        conflict = {
                            "vpc1": vpc1["VpcId"],
                            "vpc1_account": vpc1["AccountId"],
                            "vpc1_region": vpc1["Region"],
                            "vpc1_cidr": vpc1["CIDR"],
                            "vpc1_name": vpc1.get("VpcName", "No name defined"),
                            "vpc2": vpc2["VpcId"],
                            "vpc2_account": vpc2["AccountId"],
                            "vpc2_region": vpc2["Region"],
                            "vpc2_cidr": vpc2["CIDR"],
                            "vpc2_name": vpc2.get("VpcName", "No name defined"),
                            "severity": "HIGH",  # Prevents VPC peering/TGW attachment
                            "impact": "Cannot establish VPC peering or Transit Gateway attachment",
                        }
                        self.conflicts.append(conflict)

                        logging.warning(
                            f"CIDR conflict detected: {vpc1['VpcId']} ({vpc1['CIDR']}) overlaps "
                            f"{vpc2['VpcId']} ({vpc2['CIDR']})"
                        )
                except Exception as e:
                    # Handle invalid CIDR blocks gracefully
                    logging.error(f"Error checking CIDR overlap: {e}")
                    continue

        logging.info(f"CIDR conflict detection complete: {len(self.conflicts)} conflicts found")
        return self.conflicts

    def _check_cidr_overlap(self, cidr1: str, cidr2: str) -> bool:
        """
        Check if two CIDRs overlap using Python ipaddress library.

        Args:
            cidr1: First CIDR block (e.g., '10.0.0.0/16')
            cidr2: Second CIDR block (e.g., '10.0.128.0/17')

        Returns:
            True if CIDRs overlap, False otherwise

        Algorithm:
            - ipaddress.ip_network() parses CIDR notation
            - .overlaps() method checks network overlap
            - strict=False allows host bits in network addresses

        Examples:
            - '10.0.0.0/16' overlaps '10.0.128.0/17' → True
            - '10.0.0.0/16' overlaps '192.168.0.0/16' → False
            - '172.16.0.0/12' overlaps '172.31.0.0/16' → True
        """
        try:
            network1 = ipaddress.ip_network(cidr1, strict=False)
            network2 = ipaddress.ip_network(cidr2, strict=False)
            return network1.overlaps(network2)
        except ValueError as e:
            # Handle invalid CIDR format
            logging.error(f"Invalid CIDR format: {cidr1} or {cidr2} - {e}")
            return False

    def export_conflicts(self, output_file: str = "/tmp/vpc-cidr-conflicts.xlsx"):
        """
        Export CIDR conflicts to Excel for stakeholder review.

        Args:
            output_file: Output file path (default: /tmp/vpc-cidr-conflicts.xlsx)

        Output Formats:
            - .xlsx: Excel format with formatted columns
            - .csv: CSV format for programmatic processing
            - .json: JSON format for API integration

        Excel Columns:
            - VPC 1 ID, Account, Region, CIDR, Name
            - VPC 2 ID, Account, Region, CIDR, Name
            - Severity, Impact (business description)

        Business Value:
            - Enables non-technical stakeholder review
            - Supports VPC migration planning decisions
            - Documents compliance violations for remediation
        """
        if not self.conflicts:
            logging.info("No CIDR conflicts to export")
            console.print("[green]✅ No CIDR conflicts detected - all VPCs have unique address spaces[/green]")
            return

        # Create DataFrame with business-friendly column names
        conflicts_df = pd.DataFrame(self.conflicts)

        # Reorder columns for business readability
        column_order = [
            "vpc1",
            "vpc1_name",
            "vpc1_account",
            "vpc1_region",
            "vpc1_cidr",
            "vpc2",
            "vpc2_name",
            "vpc2_account",
            "vpc2_region",
            "vpc2_cidr",
            "severity",
            "impact",
        ]
        conflicts_df = conflicts_df[column_order]

        # Rename columns for executive clarity
        conflicts_df.columns = [
            "VPC 1 ID",
            "VPC 1 Name",
            "VPC 1 Account",
            "VPC 1 Region",
            "VPC 1 CIDR",
            "VPC 2 ID",
            "VPC 2 Name",
            "VPC 2 Account",
            "VPC 2 Region",
            "VPC 2 CIDR",
            "Severity",
            "Business Impact",
        ]

        # Export based on file extension
        if output_file.endswith(".xlsx"):
            conflicts_df.to_excel(output_file, index=False, engine="openpyxl")
        elif output_file.endswith(".json"):
            conflicts_df.to_json(output_file, orient="records", indent=2)
        else:  # Default to CSV
            conflicts_df.to_csv(output_file, index=False)

        logging.info(f"CIDR conflicts exported to {output_file}")
        console.print(f"[yellow]⚠️  {len(self.conflicts)} CIDR conflicts exported to {output_file}[/yellow]")


##########################
def parse_args(args):
    """
    Parse and validate command-line arguments for VPC network topology discovery.

    Configures the argument parser with VPC-specific options including default VPC
    detection for security auditing and comprehensive network inventory capabilities.
    Uses the standardized CommonArguments framework for consistency.

    Args:
        args (list): Command-line arguments to parse (typically sys.argv[1:])

    Returns:
        argparse.Namespace: Parsed arguments containing:
            - Profiles: AWS profiles for multi-account network discovery
            - Regions: Target AWS regions for VPC enumeration
            - AccessRoles: Cross-account roles for Organizations access
            - pDefault: CRITICAL security flag for default VPC identification
            - RootOnly: Limit to Organization Management Accounts
            - Filename: Output file prefix for network topology export
            - Other standard framework arguments

    Security-Critical Argument:
        --default: Identifies default VPCs which represent significant security risks:
                  - Often have overly permissive security groups
                  - May violate network segmentation policies
                  - Should be replaced with purpose-built VPCs
                  - Critical for compliance auditing (PCI DSS, SOC2)
                  - Essential for CIS benchmark compliance

    Network Architecture Use Cases:
        - Network topology mapping: Complete VPC inventory
        - Security auditing: Default VPC identification and remediation
        - CIDR planning: IP address space utilization analysis
        - Compliance validation: Network segmentation verification
        - Migration planning: Cross-account network architecture assessment
    """
    parser = CommonArguments()
    parser.my_parser.description = "We're going to find all vpcs within any of the accounts and regions we have access to, given the profile(s) provided."
    parser.multiprofile()
    parser.multiregion()
    parser.extendedargs()
    parser.rolestouse()
    parser.rootOnly()
    parser.timing()
    parser.save_to_file()
    parser.verbosity()
    parser.version(__version__)
    parser.my_parser.add_argument(
        "--default",
        dest="pDefault",
        metavar="Looking for default VPCs only",
        action="store_const",
        default=False,
        const=True,
        help="Flag to determine whether we're looking for default VPCs only.",
    )
    parser.my_parser.add_argument(
        "--detect-conflicts",
        dest="pDetectConflicts",
        action="store_const",
        default=False,
        const=True,
        help="Track 5 (v1.1.19): Detect CIDR overlaps across VPCs to validate VPC peering/TGW feasibility. "
        "Prevents network architecture violations during VPC recreation (JIRA AWSO-65).",
    )
    return parser.my_parser.parse_args(args)


def find_all_vpcs(fAllCredentials, fDefaultOnly=False):
    """
    Execute multi-threaded VPC discovery across AWS accounts and regions.

    This is the core network topology discovery engine that performs concurrent
    VPC enumeration across all provided AWS accounts and regions. Essential for
    understanding network architecture, CIDR utilization, and security posture.

    Args:
        fAllCredentials (list): List of credential dictionaries containing:
            - AccountId: AWS account identifier
            - Region: AWS region name
            - AccessKeyId, SecretAccessKey, SessionToken: AWS credentials
            - MgmtAccount: Management account identifier
            - Success: Boolean flag indicating credential validation status

        fDefaultOnly (bool, optional): Focus discovery on default VPCs only.
            Critical for security auditing as default VPCs often violate
            network security policies and compliance requirements.

    Returns:
        list: Comprehensive VPC inventory with network metadata:
            - VpcId: AWS VPC identifier
            - VpcName: VPC name from tags (or "No name defined")
            - CIDR: VPC CIDR block (handles multiple CIDRs per VPC)
            - IsDefault: Boolean indicating if VPC is account default
            - AccountId: Source AWS account
            - Region: Source AWS region
            - MgmtAccount: Management account identifier

    Threading Architecture:
        - Uses Queue for thread-safe work distribution
        - Worker thread pool for concurrent VPC discovery
        - Progress tracking for large-scale network inventory
        - Comprehensive error handling for account access failures

    Network Analysis Features:
        - CIDR block enumeration (handles secondary CIDR associations)
        - Default VPC identification for security compliance
        - Tag-based VPC naming and categorization
        - Cross-account network topology mapping
        - Regional network architecture visibility

    Security Implications:
        - Default VPCs represent significant security risks
        - Often have permissive default security groups
        - May violate network segmentation requirements
        - Critical for PCI DSS and SOC2 compliance validation
        - Essential for Zero Trust architecture assessment

    Enterprise Use Cases:
        - Network architecture documentation
        - CIDR space planning and IP address management
        - Compliance auditing and remediation planning
        - Multi-account network segmentation validation
        - Cloud migration network assessment
    """

    class FindVPCs(Thread):
        """
        Worker thread for concurrent VPC discovery and network topology analysis.

        Each worker thread processes credential sets from the shared queue,
        calls AWS EC2 VPC APIs to discover network infrastructure, and performs
        detailed CIDR and default VPC analysis for security assessment.

        Network Discovery Capabilities:
            - VPC enumeration with metadata extraction
            - CIDR block association analysis
            - Default VPC identification for security auditing
            - Tag-based VPC naming and categorization
            - Cross-account network topology mapping
        """

        def __init__(self, queue):
            """
            Initialize worker thread with reference to shared work queue.

            Args:
                queue (Queue): Thread-safe queue containing VPC discovery work items
            """
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            """
            Main worker thread execution loop for VPC network discovery.

            Continuously processes credential sets from queue, performs VPC
            discovery via AWS EC2 APIs, and aggregates network topology data
            with comprehensive CIDR and security analysis.
            """
            while True:
                # Get VPC discovery work item from thread-safe queue
                c_account_credentials, c_default, c_PlaceCount = self.queue.get()
                logging.info(f"De-queued info for account number {c_account_credentials['AccountId']}")

                try:
                    # Call AWS EC2 API to discover VPCs in this account/region
                    # find_account_vpcs2() handles DescribeVpcs API with optional default filtering
                    Vpcs = Inventory_Modules.find_account_vpcs2(c_account_credentials, c_default)

                    logging.info(
                        f"Account: {c_account_credentials['AccountId']} Region: {c_account_credentials['Region']} | Found {len(Vpcs['Vpcs'])} VPCs"
                    )
                    # Process discovered VPCs with comprehensive network metadata extraction
                    if "Vpcs" in Vpcs.keys() and len(Vpcs["Vpcs"]) > 0:
                        for y in range(len(Vpcs["Vpcs"])):
                            # Initialize VPC metadata with default values
                            VpcName = "No name defined"  # Fallback for untagged VPCs
                            VpcId = Vpcs["Vpcs"][y]["VpcId"]
                            IsDefault = Vpcs["Vpcs"][y]["IsDefault"]  # Critical for security assessment
                            CIDRBlockAssociationSet = Vpcs["Vpcs"][y]["CidrBlockAssociationSet"]

                            # Extract VPC name from tags for network documentation
                            # Proper VPC naming is essential for network governance
                            if "Tags" in Vpcs["Vpcs"][y]:
                                for z in range(len(Vpcs["Vpcs"][y]["Tags"])):
                                    if Vpcs["Vpcs"][y]["Tags"][z]["Key"] == "Name":
                                        VpcName = Vpcs["Vpcs"][y]["Tags"][z]["Value"]

                            # Handle multiple CIDR block associations per VPC
                            # AWS supports secondary CIDR blocks for IP space expansion
                            # Each CIDR gets its own record for accurate IP space tracking
                            for _ in range(len(CIDRBlockAssociationSet)):
                                # Create individual record for each CIDR association
                                # This enables precise CIDR space analysis and planning
                                AllVPCs.append(
                                    {
                                        # Organizational context
                                        "MgmtAccount": c_account_credentials["MgmtAccount"],
                                        "AccountId": c_account_credentials["AccountId"],
                                        "Region": c_account_credentials["Region"],
                                        # Network topology data
                                        "CIDR": CIDRBlockAssociationSet[_]["CidrBlock"],
                                        "VpcId": VpcId,
                                        "VpcName": VpcName,
                                        # Security-critical default VPC flag
                                        "IsDefault": IsDefault,
                                    }
                                )
                    else:
                        # No VPCs found in this account/region combination
                        continue
                except KeyError as my_Error:
                    # Handle credential or account access configuration errors
                    logging.error(f"Account Access failed - trying to access {c_account_credentials['AccountId']}")
                    logging.info(f"Actual Error: {my_Error}")
                    # Continue processing other accounts despite this failure
                    pass

                except AttributeError as my_Error:
                    # Handle profile configuration or credential format errors
                    logging.error(f"Error: Likely that one of the supplied profiles was wrong")
                    logging.warning(my_Error)
                    continue

                except ClientError as my_Error:
                    # Handle AWS API authentication and authorization errors
                    if "AuthFailure" in str(my_Error):
                        logging.error(
                            f"Authorization Failure accessing account {c_account_credentials['AccountId']} in {c_account_credentials['Region']} region"
                        )
                        logging.warning(
                            f"It's possible that the region {c_account_credentials['Region']} hasn't been opted-into"
                        )
                        continue
                    else:
                        # Handle API throttling and other service errors
                        logging.error(f"Error: Likely throttling errors from too much activity")
                        logging.warning(my_Error)
                        continue

                finally:
                    # Always mark work item as complete for queue management
                    self.queue.task_done()

    ###########

    checkqueue = Queue()

    AllVPCs = []
    PlaceCount = 0
    WorkerThreads = min(len(fAllCredentials), 25)

    worker_threads = []
    for x in range(WorkerThreads):
        worker = FindVPCs(checkqueue)
        # Setting daemon to False for proper cleanup
        worker.daemon = False
        worker.start()
        worker_threads.append(worker)

    for credential in fAllCredentials:
        logging.info(f"Beginning to queue data - starting with {credential['AccountId']}")
        console.print(
            f"Checking {credential['AccountId']} in region {credential['Region']} - {PlaceCount + 1} / {len(fAllCredentials)}",
            end="",
        )
        # for region in fRegionList:
        try:
            # I don't know why - but double parens are necessary below. If you remove them, only the first parameter is queued.
            checkqueue.put((credential, fDefaultOnly, PlaceCount))
            logging.info(f"Put credential: {credential}, Default: {fDefaultOnly}")
            PlaceCount += 1
        except ClientError as my_Error:
            if "AuthFailure" in str(my_Error):
                logging.error(
                    f"Authorization Failure accessing account {credential['AccountId']} in {credential['Region']} region"
                )
                logging.warning(f"It's possible that the region {credential['Region']} hasn't been opted-into")
                pass
    checkqueue.join()
    return AllVPCs


##########################
if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    pProfiles = args.Profiles
    pRegionList = args.Regions
    pAccounts = args.Accounts
    pRoles = args.AccessRoles
    pSkipProfiles = args.SkipProfiles
    pSkipAccounts = args.SkipAccounts
    pRootOnly = args.RootOnly
    pTiming = args.Time
    pFilename = args.Filename
    pDefault = args.pDefault
    pDetectConflicts = args.pDetectConflicts  # Track 5: CIDR conflict detection
    verbose = args.loglevel
    logging.basicConfig(level=verbose, format="[%(filename)s:%(lineno)s - %(funcName)30s() ] %(message)s")

    begin_time = time()

    NumVpcsFound = 0
    NumRegions = 0
    if pProfiles is not None:
        print(f"Checking for VPCs in profile{'s' if len(pProfiles) > 1 else ''} {pProfiles}")
    else:
        print(f"Checking for VPCs in default profile")

    # NumOfRootProfiles = 0
    # Get credentials
    AllCredentials = get_all_credentials(
        pProfiles, pTiming, pSkipProfiles, pSkipAccounts, pRootOnly, pAccounts, pRegionList, pRoles
    )
    AllRegionsList = list(set([x["Region"] for x in AllCredentials]))
    AllAccountList = list(set([x["AccountId"] for x in AllCredentials]))
    # Find the VPCs
    All_VPCs_Found = find_all_vpcs(AllCredentials, pDefault)
    # Display results
    display_dict = {
        "MgmtAccount": {"DisplayOrder": 1, "Heading": "Mgmt Acct"},
        "AccountId": {"DisplayOrder": 2, "Heading": "Acct Number"},
        "Region": {"DisplayOrder": 3, "Heading": "Region"},
        "VpcName": {"DisplayOrder": 4, "Heading": "VPC Name"},
        "CIDR": {"DisplayOrder": 5, "Heading": "CIDR Block"},
        "IsDefault": {"DisplayOrder": 6, "Heading": "Default VPC", "Condition": [True, 1, "1"]},
        "VpcId": {"DisplayOrder": 7, "Heading": "VPC Id"},
    }

    logging.info(f"# of Regions: {len(AllRegionsList)}")
    # logging.info(f"# of Management Accounts: {NumOfRootProfiles}")
    logging.info(f"# of Child Accounts: {len(AllAccountList)}")

    sorted_AllVPCs = sorted(
        All_VPCs_Found, key=lambda d: (d["MgmtAccount"], d["AccountId"], d["Region"], d["VpcName"], d["CIDR"])
    )

    # Track 5: CIDR Conflict Detection (v1.1.19)
    if pDetectConflicts:
        console.print()
        console.print("[bold blue]🔍 CIDR Conflict Detection (Track 5)[/bold blue]")
        console.print("[dim]Validating VPC CIDR overlaps for peering/Transit Gateway feasibility...[/dim]")

        # Initialize conflict detector with discovered VPCs
        detector = CIDRConflictDetector(sorted_AllVPCs)
        conflicts = detector.detect_overlaps()

        if conflicts:
            # Export conflicts to Excel for stakeholder review
            conflict_output = "/tmp/vpc-cidr-conflicts.xlsx"
            detector.export_conflicts(conflict_output)

            console.print()
            console.print(f"[yellow]⚠️  {len(conflicts)} CIDR conflict(s) detected[/yellow]")
            console.print(f"[yellow]📊 Conflict details exported to: {conflict_output}[/yellow]")
            console.print()
            console.print("[bold red]Business Impact:[/bold red]")
            console.print("  • Cannot establish VPC peering between conflicting VPCs")
            console.print("  • Cannot attach conflicting VPCs to Transit Gateway")
            console.print("  • VPN/Direct Connect routing conflicts may occur")
            console.print()
            console.print("[bold yellow]⚠️  Review conflict report before VPC recreation (JIRA AWSO-65)[/bold yellow]")
        else:
            console.print()
            console.print("[green]✅ No CIDR conflicts detected - all VPCs have unique address spaces[/green]")
            console.print("[green]✅ VPC peering and Transit Gateway attachments are feasible[/green]")

        console.print()

    print()
    display_results(sorted_AllVPCs, display_dict, None, pFilename)

    # Threading cleanup is handled within find_all_vpcs function

    print()
    # checkqueue.join() marks all of the threads as done - so Checking is done
    logging.info(f"Threads all done - took {time() - begin_time:.2f} seconds")

    if pTiming:
        console.print()
        console.print(f"[green]This script took {time() - begin_time:.2f} seconds[/green]")
    console.print()
    # Had to do this, because some of the VPCs that show up in the "sorted_AllVPCs" list are actually the same VPC, with a different CIDR range.
    Num_of_unique_VPCs = len(set([x["VpcId"] for x in sorted_AllVPCs]))
    print(
        f"Found {Num_of_unique_VPCs}{' default' if pDefault else ''} Vpcs across {len(AllAccountList)} accounts across {len(AllRegionsList)} regions"
    )
    print()
    print("Thank you for using this script.")
    print()
