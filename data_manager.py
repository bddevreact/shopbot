import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
import threading
from pathlib import Path

class DataManager:
    """Professional data management system with atomic operations and backups"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.lock = threading.Lock()
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def _get_file_path(self, filename: str) -> Path:
        """Get full file path"""
        return self.data_dir / filename
    
    def _atomic_write(self, filepath: Path, data: Any) -> bool:
        """Atomically write data to file"""
        try:
            # Write to temporary file first
            temp_file = filepath.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            temp_file.replace(filepath)
            return True
        except Exception as e:
            # Clean up temp file if it exists
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def load_data(self, filename: str, default: Any = None) -> Any:
        """Load data from file with error handling"""
        with self.lock:
            filepath = self._get_file_path(filename)
            
            try:
                if not filepath.exists():
                    if default is not None:
                        self.save_data(filename, default)
                    return default
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return default
                    return json.loads(content)
            
            except (json.JSONDecodeError, FileNotFoundError) as e:
                # Create backup of corrupted file
                if filepath.exists():
                    backup_name = f"{filename}_corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(filepath, self.backup_dir / backup_name)
                
                if default is not None:
                    self.save_data(filename, default)
                return default
    
    def save_data(self, filename: str, data: Any) -> bool:
        """Save data to file atomically"""
        with self.lock:
            filepath = self._get_file_path(filename)
            
            # Create backup before saving
            if filepath.exists():
                self._create_backup(filename)
            
            return self._atomic_write(filepath, data)
    
    def _create_backup(self, filename: str):
        """Create timestamped backup"""
        filepath = self._get_file_path(filename)
        if filepath.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{filename}_{timestamp}"
            shutil.copy2(filepath, self.backup_dir / backup_name)
    
    def create_manual_backup(self, description: str = "") -> str:
        """Create manual backup of all data files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"manual_backup_{timestamp}"
        if description:
            backup_name += f"_{description.replace(' ', '_')}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        # Copy all data files
        for file in self.data_dir.glob("*.json"):
            if file.name != "backups":
                shutil.copy2(file, backup_path / file.name)
        
        return str(backup_path)
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Get list of available backups"""
        backups = []
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                backup_info = {
                    'name': backup_dir.name,
                    'created': datetime.fromtimestamp(backup_dir.stat().st_mtime),
                    'size': sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
                }
                backups.append(backup_info)
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def restore_backup(self, backup_name: str) -> bool:
        """Restore from backup"""
        try:
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists():
                return False
            
            # Create current backup before restore
            self.create_manual_backup("before_restore")
            
            # Restore files
            for file in backup_path.glob("*.json"):
                shutil.copy2(file, self.data_dir / file.name)
            
            return True
        except Exception:
            return False
    
    def cleanup_old_backups(self, days_to_keep: int = 30):
        """Clean up old backups"""
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir() and backup_dir.stat().st_mtime < cutoff_date:
                shutil.rmtree(backup_dir)
    
    def get_data_stats(self) -> Dict[str, Any]:
        """Get statistics about data files"""
        stats = {
            'files': {},
            'total_size': 0,
            'backup_count': 0
        }
        
        # File statistics
        for file in self.data_dir.glob("*.json"):
            if file.name != "backups":
                file_stats = {
                    'size': file.stat().st_size,
                    'modified': datetime.fromtimestamp(file.stat().st_mtime),
                    'exists': True
                }
                stats['files'][file.name] = file_stats
                stats['total_size'] += file_stats['size']
        
        # Backup count
        stats['backup_count'] = len([d for d in self.backup_dir.iterdir() if d.is_dir()])
        
        return stats

# Global data manager instance
data_manager = DataManager()
