"""Resolve a local payment attempt after stopping the laboratory server."""
import argparse
from pathlib import Path

from tools.payment_lab.attempts import PaymentAttempts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--station", required=True)
    parser.add_argument("--operation-id", required=True)
    parser.add_argument("--state", choices=("APPLIED", "FAILED"), required=True)
    parser.add_argument("--evidence", required=True, help="ID de caso de soporte sin datos sensibles")
    parser.add_argument("--service-stopped", action="store_true", required=True)
    args = parser.parse_args()
    ledger = PaymentAttempts(args.ledger)
    ledger.reconcile(args.operation_id, args.station, args.state, args.evidence)
    print("Intento conciliado en el registro local.")


if __name__ == "__main__":
    main()
