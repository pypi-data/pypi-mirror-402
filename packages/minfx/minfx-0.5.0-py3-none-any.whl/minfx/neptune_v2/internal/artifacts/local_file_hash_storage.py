__all__ = ['LocalFileHashStorage']
from dataclasses import dataclass
from pathlib import Path
import sqlite3 as sql

class LocalFileHashStorage:

    @dataclass
    class LocalFileHash:
        file_path: str
        file_hash: str
        modification_date: str

    def __init__(self):
        db_path = Path.home() / '.neptune' / 'files.db'
        Path(db_path.parent).mkdir(parents=True, exist_ok=True)
        self.session = sql.connect(str(db_path))
        self.cursor = self.session.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS local_file_hashes (file_path text, file_hash text, modification_date text)')
        self.session.commit()

    def insert(self, path, computed_hash, modification_date):
        self.cursor.execute('INSERT INTO local_file_hashes (file_path, file_hash, modification_date) VALUES (?, ?, ?)', (str(path), computed_hash, modification_date))
        self.session.commit()

    def fetch_one(self, path):
        found = [LocalFileHashStorage.LocalFileHash(*row) for row in self.cursor.execute('SELECT file_path, file_hash, modification_date FROM local_file_hashes WHERE file_path = ?', (str(path),))]
        return found[0] if found is not None and len(found) > 0 else None

    def update(self, path, computed_hash, modification_date):
        self.cursor.execute('UPDATE local_file_hashes SET file_hash=?, modification_date=? WHERE file_path = ?', (computed_hash, modification_date, str(path)))
        self.session.commit()

    def close(self):
        self.session.close()