import json
from pathlib import Path
import pytest
from csvsmith.classify import CSVClassifier

@pytest.fixture
def test_data(tmp_path):
    """Sets up a temporary directory with CSV files and a config."""
    raw_dir = tmp_path / "raw"
    dest_dir = tmp_path / "output"
    raw_dir.mkdir()
    dest_dir.mkdir()

    # Create dummy CSVs
    (raw_dir / "sales_01.csv").write_text("date,item,price\n2023-01-01,hammer,15.00")
    (raw_dir / "users_01.csv").write_text("user_id,email,signup_date\n1,test@example.com,2023-01-01")
    (raw_dir / "weather.csv").write_text("temp,humidity\n22.5,45")

    sigs = {"Sales": ["date", "item", "price"], "Users": ["user_id", "email"]}
    
    return {
        "raw": raw_dir,
        "dest": dest_dir,
        "sigs": sigs
    }

def test_classifier_run(test_data):
    classifier = CSVClassifier(test_data["raw"], test_data["dest"], test_data["sigs"], auto=True)
    classifier.run()

    # Check if files moved to correct folders
    assert (test_data["dest"] / "Sales" / "sales_01.csv").exists()
    assert (test_data["dest"] / "Users" / "users_01.csv").exists()
    # Auto-cluster should create a folder based on sorted headers
    cluster_dir = next(test_data["dest"].glob("cluster_*"))
    assert (cluster_dir / "weather.csv").exists()

def test_classifier_rollback(test_data):
    classifier = CSVClassifier(test_data["raw"], test_data["dest"], test_data["sigs"])
    classifier.run()

    # Find the manifest
    manifest_path = next(test_data["dest"].glob("manifest_*.json"))
    
    # Run rollback
    classifier.rollback(manifest_path)

    # Files should be back in raw
    assert (test_data["raw"] / "sales_01.csv").exists()
    assert (test_data["raw"] / "users_01.csv").exists()
    # Output folders should be empty of the moved files (though the dirs remain)
    assert not (test_data["dest"] / "Sales" / "sales_01.csv").exists()

def test_classifier_dry_run(test_data):
    classifier = CSVClassifier(test_data["raw"], test_data["dest"], test_data["sigs"], dry_run=True)
    classifier.run()

    # Nothing should have moved
    assert (test_data["raw"] / "sales_01.csv").exists()
    assert not (test_data["dest"] / "Sales").exists()