#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import os
import pickle
import time
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
import sqlite3
import threading
from pathlib import Path

class SmartCache:
    """
    Интеллектуальная система кэширования для OCR результатов
    """
    
    def __init__(self, cache_dir: str = "cache", max_cache_size_mb: int = 500):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.max_cache_size = max_cache_size_mb * 1024 * 1024  # Конвертация в байты
        self.db_path = self.cache_dir / "cache_metadata.db"
        self.lock = threading.RLock()
        
        self._init_database()
        self._cleanup_expired()
    
    def _init_database(self):
        """Инициализация SQLite базы для метаданных кэша"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    cache_key TEXT PRIMARY KEY,
                    file_path TEXT,
                    file_hash TEXT,
                    file_size INTEGER,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    processing_time REAL,
                    ocr_quality_score REAL,
                    document_type TEXT,
                    expires_at TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_accessed 
                ON cache_entries(last_accessed)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_hash 
                ON cache_entries(file_hash)
            """)
    
    def _get_file_hash(self, file_path: str) -> str:
        """Получение хэша файла для определения изменений"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_cache_key(self, file_path: str, ocr_config: Dict) -> str:
        """Генерация ключа кэша на основе файла и конфигурации"""
        config_str = json.dumps(ocr_config, sort_keys=True)
        combined = f"{file_path}:{config_str}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Путь к файлу кэша"""
        return self.cache_dir / f"{cache_key}.pkl"
    
    def is_cached(self, file_path: str, ocr_config: Dict) -> bool:
        """Проверка наличия актуального кэша"""
        if not os.path.exists(file_path):
            return False
        
        cache_key = self._get_cache_key(file_path, ocr_config)
        cache_file = self._get_cache_file_path(cache_key)
        
        if not cache_file.exists():
            return False
        
        # Проверяем актуальность по хэшу файла
        current_hash = self._get_file_hash(file_path)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT file_hash, expires_at FROM cache_entries WHERE cache_key = ?",
                (cache_key,)
            )
            result = cursor.fetchone()
            
            if not result:
                return False
            
            stored_hash, expires_at = result
            expires_dt = datetime.fromisoformat(expires_at) if expires_at else None
            
            # Проверяем хэш и срок действия
            if stored_hash != current_hash:
                self._remove_cache_entry(cache_key)
                return False
            
            if expires_dt and datetime.now() > expires_dt:
                self._remove_cache_entry(cache_key)
                return False
        
        return True
    
    def get_cached_result(self, file_path: str, ocr_config: Dict) -> Optional[Dict]:
        """Получение результата из кэша"""
        if not self.is_cached(file_path, ocr_config):
            return None
        
        cache_key = self._get_cache_key(file_path, ocr_config)
        cache_file = self._get_cache_file_path(cache_key)
        
        try:
            with open(cache_file, 'rb') as f:
                result = pickle.load(f)
            
            # Обновляем статистику доступа
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE cache_entries 
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE cache_key = ?
                """, (datetime.now().isoformat(), cache_key))
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка чтения кэша: {e}")
            self._remove_cache_entry(cache_key)
            return None
    
    def cache_result(self, file_path: str, ocr_config: Dict, result: Dict, 
                    processing_time: float = 0, quality_score: float = 0,
                    document_type: str = 'unknown', ttl_hours: int = 24) -> bool:
        """Сохранение результата в кэш"""
        
        try:
            cache_key = self._get_cache_key(file_path, ocr_config)
            cache_file = self._get_cache_file_path(cache_key)
            
            # Сохраняем данные
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
            
            # Метаданные
            file_hash = self._get_file_hash(file_path)
            file_size = os.path.getsize(file_path)
            now = datetime.now()
            expires_at = now + timedelta(hours=ttl_hours)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries
                    (cache_key, file_path, file_hash, file_size, created_at, 
                     last_accessed, processing_time, ocr_quality_score, 
                     document_type, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cache_key, file_path, file_hash, file_size,
                    now.isoformat(), now.isoformat(), processing_time,
                    quality_score, document_type, expires_at.isoformat()
                ))
            
            # Проверяем размер кэша
            self._manage_cache_size()
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения в кэш: {e}")
            return False
    
    def _remove_cache_entry(self, cache_key: str):
        """Удаление записи из кэша"""
        cache_file = self._get_cache_file_path(cache_key)
        
        if cache_file.exists():
            cache_file.unlink()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache_entries WHERE cache_key = ?", (cache_key,))
    
    def _cleanup_expired(self):
        """Очистка просроченных записей"""
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Получаем просроченные ключи
            cursor = conn.execute(
                "SELECT cache_key FROM cache_entries WHERE expires_at < ?",
                (now,)
            )
            expired_keys = [row[0] for row in cursor.fetchall()]
            
            # Удаляем файлы и записи
            for cache_key in expired_keys:
                self._remove_cache_entry(cache_key)
            
            print(f"🧹 Очищено просроченных записей: {len(expired_keys)}")
    
    def _manage_cache_size(self):
        """Управление размером кэша"""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl"))
        
        if total_size > self.max_cache_size:
            # Удаляем старые и редко используемые записи
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT cache_key, file_size, last_accessed, access_count
                    FROM cache_entries
                    ORDER BY 
                        (julianday('now') - julianday(last_accessed)) * 
                        (1.0 / (access_count + 1)) DESC
                """)
                
                size_to_remove = total_size - (self.max_cache_size * 0.8)  # Оставляем 80%
                removed_size = 0
                
                for cache_key, file_size, last_accessed, access_count in cursor:
                    if removed_size >= size_to_remove:
                        break
                    
                    self._remove_cache_entry(cache_key)
                    removed_size += file_size
                
                print(f"🧹 Освобождено места в кэше: {removed_size / 1024 / 1024:.1f} MB")
    
    def get_cache_stats(self) -> Dict:
        """Статистика кэша"""
        with sqlite3.connect(self.db_path) as conn:
            # Общая статистика
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(file_size) as total_file_size,
                    AVG(processing_time) as avg_processing_time,
                    AVG(ocr_quality_score) as avg_quality,
                    SUM(access_count) as total_accesses
                FROM cache_entries
            """)
            general_stats = cursor.fetchone()
            
            # Статистика по типам документов
            cursor = conn.execute("""
                SELECT document_type, COUNT(*), AVG(ocr_quality_score)
                FROM cache_entries
                GROUP BY document_type
            """)
            type_stats = cursor.fetchall()
            
            # Размер кэш-файлов
            cache_file_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl"))
            
            return {
                'total_entries': general_stats[0] or 0,
                'total_source_size_mb': (general_stats[1] or 0) / 1024 / 1024,
                'cache_size_mb': cache_file_size / 1024 / 1024,
                'avg_processing_time': general_stats[2] or 0,
                'avg_quality_score': general_stats[3] or 0,
                'total_accesses': general_stats[4] or 0,
                'cache_efficiency': cache_file_size / max(general_stats[1] or 1, 1),
                'document_types': {
                    doc_type: {'count': count, 'avg_quality': avg_quality}
                    for doc_type, count, avg_quality in type_stats
                }
            }
    
    def clear_cache(self, older_than_hours: Optional[int] = None):
        """Очистка кэша"""
        if older_than_hours:
            cutoff_time = (datetime.now() - timedelta(hours=older_than_hours)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT cache_key FROM cache_entries WHERE created_at < ?",
                    (cutoff_time,)
                )
                old_keys = [row[0] for row in cursor.fetchall()]
                
                for cache_key in old_keys:
                    self._remove_cache_entry(cache_key)
                
                print(f"🧹 Удалено записей старше {older_than_hours}ч: {len(old_keys)}")
        else:
            # Полная очистка
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache_entries")
            
            print("🧹 Кэш полностью очищен")

# Демонстрация использования
def demo_smart_cache():
    """Демонстрация интеллектуального кэширования"""
    
    print("🚀 ДЕМОНСТРАЦИЯ ИНТЕЛЛЕКТУАЛЬНОГО КЭШИРОВАНИЯ")
    print("=" * 50)
    
    cache = SmartCache(cache_dir="OCR/cache", max_cache_size_mb=100)
    
    # Статистика
    stats = cache.get_cache_stats()
    print("📊 Статистика кэша:")
    print(f"   📁 Записей в кэше: {stats['total_entries']}")
    print(f"   💾 Размер кэша: {stats['cache_size_mb']:.1f} MB")
    print(f"   ⚡ Среднее время обработки: {stats['avg_processing_time']:.2f}с")
    print(f"   🎯 Средняя оценка качества: {stats['avg_quality_score']:.1f}")
    print(f"   📈 Эффективность сжатия: {stats['cache_efficiency']:.2f}")
    
    if stats['document_types']:
        print("\n📋 По типам документов:")
        for doc_type, type_stats in stats['document_types'].items():
            print(f"   {doc_type}: {type_stats['count']} документов, качество {type_stats['avg_quality']:.1f}")
    
    # Тестирование кэширования
    test_file = "_Sources/Ontology PIK/PIK-5-Core-Kit/PIK 5-0 - Ecosystem Forces Scan - ENG.pdf"
    
    if os.path.exists(test_file):
        ocr_config = {
            'engine': 'tesseract',
            'language': 'eng+rus',
            'psm': 6,
            'preprocessing': 'enhanced'
        }
        
        print(f"\n🔍 Проверка кэша для: {os.path.basename(test_file)}")
        
        # Проверяем наличие в кэше
        is_cached = cache.is_cached(test_file, ocr_config)
        print(f"💾 В кэше: {'Да' if is_cached else 'Нет'}")
        
        if is_cached:
            print("⚡ Загрузка из кэша...")
            start_time = time.time()
            cached_result = cache.get_cached_result(test_file, ocr_config)
            load_time = time.time() - start_time
            
            if cached_result:
                print(f"✅ Загружено за {load_time:.3f}с")
                print(f"📄 Размер результата: {len(str(cached_result))} символов")
            else:
                print("❌ Ошибка загрузки из кэша")
        else:
            print("🔄 Результат отсутствует в кэше")
            
            # Имитация OCR обработки и сохранения в кэш
            print("🔄 Имитация OCR обработки...")
            mock_result = {
                'text': 'Пример OCR результата для тестирования кэша',
                'images': ['image1.png', 'image2.png'],
                'tables': [{'rows': 5, 'cols': 3}],
                'structure': {'categories': ['ENVIRONMENT', 'MARKET']},
                'processing_info': {
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0'
                }
            }
            
            processing_time = 2.5  # Имитация времени обработки
            quality_score = 85.0
            
            success = cache.cache_result(
                test_file, ocr_config, mock_result,
                processing_time=processing_time,
                quality_score=quality_score,
                document_type='pik_diagram',
                ttl_hours=24
            )
            
            print(f"💾 Сохранение в кэш: {'Успешно' if success else 'Ошибка'}")
    
    print(f"\n📊 Обновленная статистика:")
    updated_stats = cache.get_cache_stats()
    print(f"   📁 Записей: {updated_stats['total_entries']}")
    print(f"   💾 Размер: {updated_stats['cache_size_mb']:.1f} MB")

if __name__ == "__main__":
    demo_smart_cache()
