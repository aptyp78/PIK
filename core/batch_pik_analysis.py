#!/usr/bin/env python3
"""
Batch анализ PIK фреймворков
===========================

Демонстрация пакетного анализа нескольких PIK фреймворков
с созданием сводной аналитики по всей методологии.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any

# Добавляем текущую директорию в путь для импорта
sys.path.append(str(Path(__file__).parent))

try:
    from intelligent_pik_parser import IntelligentPIKParser, PIKFramework, PIKFrameworkType
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def find_all_pik_images() -> List[str]:
    """Находит все доступные PIK изображения"""
    search_dirs = [
        "_Sources/Ontology PIK/PIK-5-Core-Kit/",
        "_Sources/Ontology PIK/PIK-5-Extended-Core-Kit/",
        "OCR/attachment_image/"
    ]
    
    found_images = []
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        full_path = os.path.join(root, file)
                        found_images.append(full_path)
    
    return found_images

def analyze_multiple_frameworks(parser: IntelligentPIKParser, image_paths: List[str], max_count: int = 5) -> List[PIKFramework]:
    """Анализирует несколько PIK фреймворков"""
    frameworks = []
    
    print(f"🔍 Начинаем пакетный анализ {min(len(image_paths), max_count)} PIK фреймворков:")
    print("=" * 70)
    
    for i, image_path in enumerate(image_paths[:max_count], 1):
        print(f"\n📊 [{i}/{min(len(image_paths), max_count)}] Анализируем: {os.path.basename(image_path)}")
        
        try:
            start_time = time.time()
            framework = parser.parse_pik_image(image_path)
            analysis_time = time.time() - start_time
            
            frameworks.append(framework)
            
            print(f"  ✅ Тип: {framework.type.value}")
            print(f"  📝 Название: {framework.title}")
            print(f"  🔢 Элементов: {len(framework.elements)}")
            print(f"  🔗 Связей: {len(framework.relationships)}")
            print(f"  ⏱️  Время: {analysis_time:.2f}с")
            print(f"  🎯 Уверенность: {framework.metadata['confidence_score']:.1%}")
            
        except Exception as e:
            print(f"  ❌ Ошибка: {str(e)}")
            continue
    
    return frameworks

def create_methodology_summary(frameworks: List[PIKFramework]) -> Dict[str, Any]:
    """Создает сводку по всей методологии PIK"""
    summary = {
        "total_frameworks": len(frameworks),
        "framework_types": {},
        "total_elements": 0,
        "total_relationships": 0,
        "avg_confidence": 0.0,
        "coverage_analysis": {},
        "lifecycle_progression": [],
        "automation_opportunities": []
    }
    
    # Анализируем распределение по типам
    type_counts = {}
    total_confidence = 0
    
    for framework in frameworks:
        # Типы фреймворков
        fw_type = framework.type.value
        if fw_type not in type_counts:
            type_counts[fw_type] = 0
        type_counts[fw_type] += 1
        
        # Общая статистика
        summary["total_elements"] += len(framework.elements)
        summary["total_relationships"] += len(framework.relationships)
        total_confidence += framework.metadata["confidence_score"]
        
        # Анализ элементов
        element_types = {}
        for element in framework.elements:
            elem_type = element.type.value
            element_types[elem_type] = element_types.get(elem_type, 0) + 1
        
        summary["framework_types"][fw_type] = {
            "count": type_counts[fw_type],
            "elements": len(framework.elements),
            "relationships": len(framework.relationships),
            "confidence": framework.metadata["confidence_score"],
            "element_distribution": element_types,
            "completeness": framework.semantic_analysis.get("framework_completeness", {}).get("score", 0),
            "methodology_alignment": framework.semantic_analysis.get("methodology_alignment", {}).get("score", 0)
        }
    
    # Средняя уверенность
    if frameworks:
        summary["avg_confidence"] = total_confidence / len(frameworks)
    
    # Анализ покрытия PIK жизненного цикла
    expected_stages = [
        PIKFrameworkType.ECOSYSTEM_FORCES,
        PIKFrameworkType.NFX_ENGINES,
        PIKFrameworkType.BUSINESS_MODEL,
        PIKFrameworkType.PLATFORM_EXPERIENCE,
        PIKFrameworkType.VALUE_NETWORK
    ]
    
    found_stages = set(fw.type for fw in frameworks)
    coverage = len(found_stages.intersection(expected_stages)) / len(expected_stages)
    
    summary["coverage_analysis"] = {
        "lifecycle_coverage": coverage,
        "found_stages": [stage.value for stage in found_stages],
        "missing_stages": [stage.value for stage in set(expected_stages) - found_stages],
        "additional_frameworks": [stage.value for stage in found_stages if stage not in expected_stages]
    }
    
    # Возможности автоматизации
    all_opportunities = []
    for framework in frameworks:
        if "automation_opportunities" in framework.semantic_analysis:
            all_opportunities.extend(framework.semantic_analysis["automation_opportunities"])
    
    # Группируем по типам
    opp_types = {}
    for opp in all_opportunities:
        opp_type = opp["type"]
        if opp_type not in opp_types:
            opp_types[opp_type] = {
                "count": 0,
                "description": opp["description"],
                "avg_impact": opp["impact"],
                "avg_complexity": opp["complexity"]
            }
        opp_types[opp_type]["count"] += 1
    
    summary["automation_opportunities"] = opp_types
    
    return summary

def print_methodology_analysis(summary: Dict[str, Any]):
    """Выводит сводный анализ методологии PIK"""
    print(f"\n" + "="*70)
    print(f"📈 СВОДНЫЙ АНАЛИЗ PIK МЕТОДОЛОГИИ")
    print(f"="*70)
    
    print(f"\n📊 Общая статистика:")
    print(f"  🔢 Проанализировано фреймворков: {summary['total_frameworks']}")
    print(f"  📝 Всего элементов извлечено: {summary['total_elements']:,}")
    print(f"  🔗 Всего связей найдено: {summary['total_relationships']:,}")
    print(f"  🎯 Средняя уверенность: {summary['avg_confidence']:.1%}")
    
    print(f"\n🎯 Покрытие PIK жизненного цикла:")
    coverage = summary["coverage_analysis"]
    print(f"  📋 Покрытие основных этапов: {coverage['lifecycle_coverage']:.1%}")
    
    if coverage["found_stages"]:
        print(f"  ✅ Найденные этапы:")
        for stage in coverage["found_stages"]:
            print(f"    • {stage}")
    
    if coverage["missing_stages"]:
        print(f"  ❌ Отсутствующие этапы:")
        for stage in coverage["missing_stages"]:
            print(f"    • {stage}")
    
    print(f"\n📈 Анализ по типам фреймворков:")
    for fw_type, data in summary["framework_types"].items():
        print(f"  🎯 {fw_type}:")
        print(f"    📊 Элементов: {data['elements']:,}, Связей: {data['relationships']:,}")
        print(f"    🎯 Уверенность: {data['confidence']:.1%}")
        print(f"    📋 Полнота: {data['completeness']:.1%}")
        print(f"    ✅ Соответствие PIK: {data['methodology_alignment']:.1%}")
    
    if summary["automation_opportunities"]:
        print(f"\n🤖 Возможности автоматизации:")
        for opp_type, data in summary["automation_opportunities"].items():
            print(f"  • {opp_type}: {data['count']} случаев (влияние: {data['avg_impact']})")

def save_batch_results(frameworks: List[PIKFramework], summary: Dict[str, Any], output_dir: str = "output"):
    """Сохраняет результаты пакетного анализа"""
    batch_dir = f"{output_dir}/batch_analysis"
    os.makedirs(batch_dir, exist_ok=True)
    
    # Сохраняем сводку
    summary_path = f"{batch_dir}/methodology_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    
    # Создаем индексный файл
    index_data = {
        "analysis_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_frameworks": len(frameworks),
        "frameworks": []
    }
    
    for framework in frameworks:
        index_data["frameworks"].append({
            "id": framework.id,
            "type": framework.type.value,
            "title": framework.title,
            "elements_count": len(framework.elements),
            "relationships_count": len(framework.relationships),
            "confidence": framework.metadata["confidence_score"],
            "files": {
                "analysis": f"analysis/{framework.id}_analysis.json",
                "report": f"analysis/{framework.id}_report.md",
                "drawio": f"drawio/{framework.id}_diagram.drawio"
            }
        })
    
    index_path = f"{batch_dir}/frameworks_index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    # Создаем сводный отчет
    report_content = f"""# PIK Methodology Batch Analysis Report

**Дата анализа:** {time.strftime("%Y-%m-%d %H:%M:%S")}  
**Всего фреймворков:** {len(frameworks)}  
**Общее количество элементов:** {summary['total_elements']:,}  
**Общее количество связей:** {summary['total_relationships']:,}  
**Средняя уверенность:** {summary['avg_confidence']:.1%}  

## Проанализированные фреймворки

"""
    
    for framework in frameworks:
        report_content += f"""### {framework.title} ({framework.type.value})
- **ID:** {framework.id}
- **Элементов:** {len(framework.elements)}
- **Связей:** {len(framework.relationships)}
- **Уверенность:** {framework.metadata['confidence_score']:.1%}
- **Файлы:** [JSON](analysis/{framework.id}_analysis.json) | [Отчет](analysis/{framework.id}_report.md) | [Draw.io](drawio/{framework.id}_diagram.drawio)

"""
    
    report_content += f"""
## Покрытие PIK жизненного цикла

**Общее покрытие:** {summary['coverage_analysis']['lifecycle_coverage']:.1%}

### Найденные этапы:
"""
    for stage in summary['coverage_analysis']['found_stages']:
        report_content += f"- ✅ {stage}\n"
    
    if summary['coverage_analysis']['missing_stages']:
        report_content += "\n### Отсутствующие этапы:\n"
        for stage in summary['coverage_analysis']['missing_stages']:
            report_content += f"- ❌ {stage}\n"
    
    report_path = f"{batch_dir}/batch_analysis_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n💾 Результаты пакетного анализа сохранены:")
    print(f"  📊 Сводка: {summary_path}")
    print(f"  📋 Индекс: {index_path}")
    print(f"  📄 Отчет: {report_path}")

def main():
    """Главная функция пакетного анализа"""
    print("🚀 PIK METHODOLOGY BATCH ANALYSIS")
    print("=" * 50)
    
    # Инициализируем парсер
    parser = IntelligentPIKParser()
    
    # Находим все PIK изображения
    all_images = find_all_pik_images()
    print(f"🔍 Найдено {len(all_images)} PIK изображений")
    
    if not all_images:
        print("❌ PIK изображения не найдены")
        return
    
    # Анализируем фреймворки
    frameworks = analyze_multiple_frameworks(parser, all_images, max_count=5)
    
    if not frameworks:
        print("❌ Не удалось проанализировать ни одного фреймворка")
        return
    
    # Сохраняем индивидуальные результаты
    print(f"\n💾 Сохранение индивидуальных результатов...")
    for framework in frameworks:
        try:
            parser.save_analysis_results(framework)
        except Exception as e:
            print(f"⚠️  Ошибка сохранения {framework.id}: {e}")
    
    # Создаем сводную аналитику
    summary = create_methodology_summary(frameworks)
    
    # Выводим анализ
    print_methodology_analysis(summary)
    
    # Сохраняем пакетные результаты
    save_batch_results(frameworks, summary)
    
    print(f"\n🎉 Пакетный анализ завершен успешно!")
    print(f"📊 Проанализировано: {len(frameworks)} фреймворков")
    print(f"📁 Результаты в: output/batch_analysis/")

if __name__ == "__main__":
    main()
