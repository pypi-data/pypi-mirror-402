"""
Command Line Interface for the Kipu API Python library
Provides utility commands for testing and managing the library
"""

import argparse
import asyncio
import json
import os
import sys

from . import KipuClient, __version__
from .exceptions import KipuAPIError


def get_credentials_from_env() -> tuple:
    """Get credentials from environment variables"""
    access_id = os.getenv("KIPU_ACCESS_ID")
    secret_key = os.getenv("KIPU_SECRET_KEY")
    app_id = os.getenv("KIPU_APP_ID")

    if not all([access_id, secret_key, app_id]):
        print("❌ Missing credentials. Please set environment variables:")
        print("   KIPU_ACCESS_ID")
        print("   KIPU_SECRET_KEY")
        print("   KIPU_APP_ID")
        sys.exit(1)

    return access_id, secret_key, app_id


async def test_connection(args) -> None:
    """Test connection to Kipu API"""
    print("🔗 Testing Kipu API connection...")

    access_id, secret_key, app_id = get_credentials_from_env()

    try:
        async with KipuClient(access_id, secret_key, app_id) as client:
            # Try to get a small amount of data
            result = await client.get_patients_census(params={"per": 1}, flatten=False)
            print("✅ Connection successful!")
            print(f"📊 Response type: {type(result)}")
            if isinstance(result, list) and result:
                print(f"📝 Sample keys: {list(result[0].keys())[:5]}...")
            elif isinstance(result, dict):
                print(f"📝 Response keys: {list(result.keys())[:5]}...")

    except KipuAPIError as e:
        print(f"❌ API Error: {e.message}")
        print(f"   Status Code: {e.status_code}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        sys.exit(1)


async def get_patients_census(args) -> None:
    """Get patients census"""
    print("👥 Fetching patients census...")

    access_id, secret_key, app_id = get_credentials_from_env()

    try:
        async with KipuClient(access_id, secret_key, app_id) as client:
            params = {}
            if args.per:
                params["per"] = args.per
            if args.page:
                params["page"] = args.page
            if args.phi_level:
                params["phi_level"] = args.phi_level

            result = await client.get_patients_census(
                params=params, flatten=not args.raw
            )

            if args.raw:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(f"📊 Retrieved {len(result)} records")
                print(f"📋 Columns: {list(result.columns)}")
                if not result.empty:
                    print("\n🔍 Sample data:")
                    print(result.head())

    except KipuAPIError as e:
        print(f"❌ API Error: {e.message}")
        sys.exit(1)


async def get_vital_signs(args) -> None:
    """Get vital signs"""
    print("📈 Fetching vital signs...")

    access_id, secret_key, app_id = get_credentials_from_env()

    try:
        async with KipuClient(access_id, secret_key, app_id) as client:
            if args.patient_id:
                result = await client.get_patient_vital_signs(
                    args.patient_id, flatten=not args.raw
                )
                print(f"📊 Vital signs for patient {args.patient_id}")
            else:
                result = await client.get_vital_signs(flatten=not args.raw)
                print("📊 All vital signs")

            if args.raw:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(f"📊 Retrieved {len(result)} records")
                if not result.empty:
                    print(f"📋 Columns: {list(result.columns)}")
                    print("\n🔍 Sample data:")
                    print(result.head())

    except KipuAPIError as e:
        print(f"❌ API Error: {e.message}")
        sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Kipu API library Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kipu-cli test                           # Test API connection
  kipu-cli census --per 10               # Get 10 patients
  kipu-cli census --raw                  # Get raw JSON response
  kipu-cli vitals                        # Get all vital signs
  kipu-cli vitals --patient-id 123       # Get vitals for specific patient

Environment Variables:
  KIPU_ACCESS_ID     Your Kipu access ID
  KIPU_SECRET_KEY    Your Kipu secret key
  KIPU_APP_ID        Your Kipu app ID
        """,
    )

    parser.add_argument(
        "--version", action="version", version=f"kipu-python {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test API connection")
    test_parser.set_defaults(func=test_connection)

    # Census command
    census_parser = subparsers.add_parser("census", help="Get patients census")
    census_parser.add_argument("--per", type=int, help="Number of records per page")
    census_parser.add_argument("--page", type=int, help="Page number")
    census_parser.add_argument(
        "--phi-level", choices=["high", "medium", "low"], help="PHI level"
    )
    census_parser.add_argument(
        "--raw", action="store_true", help="Return raw JSON response"
    )
    census_parser.set_defaults(func=get_patients_census)

    # Vital signs command
    vitals_parser = subparsers.add_parser("vitals", help="Get vital signs")
    vitals_parser.add_argument("--patient-id", help="Get vitals for specific patient")
    vitals_parser.add_argument(
        "--raw", action="store_true", help="Return raw JSON response"
    )
    vitals_parser.set_defaults(func=get_vital_signs)

    return parser


def main() -> None:
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    print(f"🏥 Kipu API library CLI v{__version__}")
    print("=" * 50)

    try:
        asyncio.run(args.func(args))
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
