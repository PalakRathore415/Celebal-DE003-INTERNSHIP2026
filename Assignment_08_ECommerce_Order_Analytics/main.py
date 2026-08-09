"""One-command runner for the complete internship mini project."""

from src.data_generator import generate_all
from src.data_cleaning import save_cleaned
from src.database import create_database
from src.sql_analysis import run_all_analysis


def main() -> None:
    """Execute generation -> cleaning -> database -> analytics."""
    print("\n[1/4] Generating raw data...")
    generate_all()

    print("\n[2/4] Cleaning and validating data...")
    save_cleaned()

    print("\n[3/4] Creating SQLite database...")
    create_database()

    print("\n[4/4] Running SQL analytics...")
    run_all_analysis()

    print("\nPipeline completed successfully.")
    print("Next: python -m src.reporting_cli")
    print("Tests: pytest -q")


if __name__ == "__main__":
    main()
