import csv
import json
import shutil
from datetime import datetime
from pathlib import Path


class CSVClassifier:
    """
    Classifies CSV files into folders based on header signatures.
    Supports predefined mapping, auto-discovery, dry-runs, and rollbacks.
    """

    def __init__(self, source_dir, dest_dir, signatures=None, auto=False, dry_run=False):
        self.source = Path(source_dir)
        self.dest = Path(dest_dir)
        self.signatures = signatures or {}
        self.auto = auto
        self.dry_run = dry_run
        self.manifest = {
            "source_path": str(self.source.absolute()),
            "timestamp": datetime.now().isoformat(),
            "operations": []
        }

    def _get_headers(self, file_path):
        """Validates if file is a CSV and extracts the first row as a header."""
        if not file_path.suffix.lower() == '.csv':
            return None
        try:
            with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.reader(f)
                header = next(reader, None)

                if not header:
                    return None

                # Rule: If the first row is purely numeric, it is data, not a header.
                if all(str(c).strip().replace('.', '', 1).isdigit() for c in header if c.strip()):
                    return None

                return [h.strip() for h in header if h.strip()]
        except (UnicodeDecodeError, csv.Error):
            return None

    def _move_file(self, file_path, category, headers):
        """Executes move with duplicate protection and records in manifest."""
        target_dir = self.dest / category
        dest_file = target_dir / file_path.name

        # Handle duplicate filenames in destination
        if dest_file.exists() and not self.dry_run:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            dest_file = target_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"

        operation_log = {
            "original_path": str(file_path.absolute()),
            "moved_to": str(dest_file.absolute()) if not self.dry_run else "simulated",
            "category": category,
            "headers": headers,
            "status": "pending"
        }

        if self.dry_run:
            print(f"[DRY RUN] Would move: {file_path.name} -> {category}/")
            operation_log["status"] = "simulated"
        else:
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(dest_file))
                print(f"Moved: {file_path.name} -> {category}/")
                operation_log["status"] = "success"
            except Exception as e:
                print(f"Failed to move {file_path.name}: {e}")
                operation_log["status"] = "failed"

        self.manifest["operations"].append(operation_log)

    def _save_manifest(self):
        """Saves the session manifest to the destination directory."""
        if not self.manifest["operations"] or self.dry_run:
            return

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        manifest_path = self.dest / f"manifest_{ts}.json"

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=4)
        print(f"\nManifest saved: {manifest_path}")

    def rollback(self, manifest_path):
        """Reverses operations defined in a manifest file."""
        m_path = Path(manifest_path)
        if not m_path.exists():
            print(f"Error: Manifest {manifest_path} not found.")
            return

        with open(m_path, 'r') as f:
            data = json.load(f)

        print(f"Starting rollback for session: {data.get('timestamp')}")
        for op in data.get("operations", []):
            if op["status"] != "success":
                continue

            current_loc = Path(op["moved_to"])
            original_loc = Path(op["original_path"])

            if current_loc.exists():
                if self.dry_run:
                    print(f"[DRY RUN] Would restore: {current_loc.name} -> {original_loc}")
                else:
                    original_loc.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(current_loc), str(original_loc))
                    print(f"Restored: {current_loc.name}")
            else:
                print(f"Warning: Could not find file to restore: {current_loc}")

    def run(self):
        """Standard classification run."""
        if not self.source.is_dir():
            print(f"Error: Source directory {self.source} does not exist.")
            return

        for file in self.source.glob("*.csv"):
            headers = self._get_headers(file)
            target_sub = "unclassified"

            if headers:
                match_found = False
                for cat, reqs in self.signatures.items():
                    if all(r in headers for r in reqs):
                        target_sub = cat
                        match_found = True
                        break

                if not match_found and self.auto:
                    slug = "_".join(sorted(headers))[:50]
                    target_sub = f"cluster_{slug}"

            self._move_file(file, target_sub, headers)

        self._save_manifest()
