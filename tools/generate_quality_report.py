#!/usr/bin/env python3
"""
HTML Report Generator for Draw.io Quality Testing
================================================

Генератор красивых HTML отчетов для результатов тестирования качества Draw.io файлов
"""

import json
import os
from datetime import datetime
from typing import List, Dict

class HTMLReportGenerator:
    """Генератор HTML отчетов"""
    
    def __init__(self):
        self.template_css = """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1a202c; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 3rem 0; }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 2rem; }
        .header h1 { font-size: 3rem; margin-bottom: 1rem; font-weight: 700; }
        .header .subtitle { font-size: 1.2rem; opacity: 0.9; }
        .main-content { padding: 3rem 0; }
        .executive-summary { background: white; padding: 2rem; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin-bottom: 3rem; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin: 2rem 0; }
        .metric-card { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 2rem; border-radius: 12px; text-align: center; }
        .metric-value { font-size: 3rem; font-weight: bold; margin-bottom: 0.5rem; }
        .metric-label { font-size: 1rem; opacity: 0.9; }
        .quality-distribution { margin: 2rem 0; }
        .quality-bar { height: 20px; border-radius: 10px; background: #e2e8f0; margin: 0.5rem 0; position: relative; overflow: hidden; }
        .quality-fill { height: 100%; transition: width 0.5s ease; }
        .quality-excellent { background: linear-gradient(90deg, #48bb78, #38a169); }
        .quality-good { background: linear-gradient(90deg, #ed8936, #dd6b20); }
        .quality-poor { background: linear-gradient(90deg, #f56565, #e53e3e); }
        .file-reports { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 2rem; margin-top: 3rem; }
        .file-card { background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.1); transition: transform 0.3s; }
        .file-card:hover { transform: translateY(-5px); }
        .file-header { padding: 1.5rem; background: #f7fafc; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }
        .file-title { font-size: 1.1rem; font-weight: 600; color: #2d3748; }
        .score-badge { padding: 0.5rem 1rem; border-radius: 20px; font-weight: bold; font-size: 0.9rem; }
        .score-excellent { background: #c6f6d5; color: #22543d; }
        .score-good { background: #feebc8; color: #9c4221; }
        .score-poor { background: #fed7d7; color: #742a2a; }
        .file-content { padding: 2rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem; }
        .stat-item { text-align: center; padding: 1rem; background: #f7fafc; border-radius: 8px; }
        .stat-value { font-size: 1.5rem; font-weight: bold; color: #4a5568; }
        .stat-label { font-size: 0.8rem; color: #718096; margin-top: 0.25rem; }
        .test-results { margin: 2rem 0; }
        .test-category { margin-bottom: 1.5rem; }
        .test-category h4 { color: #4a5568; margin-bottom: 0.5rem; font-size: 1rem; }
        .test-badges { display: flex; flex-wrap: wrap; gap: 0.5rem; }
        .test-badge { padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; font-weight: 500; }
        .test-passed { background: #c6f6d5; color: #22543d; }
        .test-failed { background: #fed7d7; color: #742a2a; }
        .issues-section { margin-top: 2rem; }
        .issue-category { margin-bottom: 1rem; }
        .issue-item { padding: 1rem; margin: 0.5rem 0; border-left: 4px solid; border-radius: 0 8px 8px 0; font-size: 0.9rem; }
        .issue-critical { background: #fed7d7; border-color: #e53e3e; }
        .issue-high { background: #feebc8; border-color: #dd6b20; }
        .issue-medium { background: #bee3f8; border-color: #3182ce; }
        .issue-low { background: #c6f6d5; border-color: #38a169; }
        .issue-title { font-weight: 600; margin-bottom: 0.25rem; }
        .issue-description { color: #4a5568; margin-bottom: 0.5rem; }
        .issue-suggestion { color: #718096; font-size: 0.8rem; font-style: italic; }
        .auto-fix-badge { background: #e6fffa; color: #234e52; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; margin-left: 0.5rem; }
        .recommendations { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 16px; margin-top: 3rem; }
        .recommendations h3 { margin-bottom: 1rem; }
        .recommendations ul { list-style: none; }
        .recommendations li { margin: 0.5rem 0; padding-left: 1.5rem; position: relative; }
        .recommendations li:before { content: '✨'; position: absolute; left: 0; }
        .footer { text-align: center; padding: 2rem; color: #718096; font-size: 0.9rem; }
        @media (max-width: 768px) {
            .container { padding: 0 1rem; }
            .header h1 { font-size: 2rem; }
            .metrics-grid { grid-template-columns: repeat(2, 1fr); }
            .file-reports { grid-template-columns: 1fr; }
        }
        """
    
    def generate_html_report(self, reports_data: List[Dict], output_path: str):
        """Генерация полного HTML отчета"""
        
        # Подсчет статистики
        total_files = len(reports_data)
        avg_score = sum(r['overall_score'] for r in reports_data) / total_files if total_files > 0 else 0
        total_issues = sum(len(r['issues']) for r in reports_data)
        
        # Распределение по качеству
        excellent = sum(1 for r in reports_data if r['overall_score'] >= 80)
        good = sum(1 for r in reports_data if 60 <= r['overall_score'] < 80)
        poor = sum(1 for r in reports_data if r['overall_score'] < 60)
        
        # Подсчет проблем по серьезности
        critical_issues = sum(sum(1 for issue in r['issues'] if issue['severity'] == 'critical') for r in reports_data)
        high_issues = sum(sum(1 for issue in r['issues'] if issue['severity'] == 'high') for r in reports_data)
        medium_issues = sum(sum(1 for issue in r['issues'] if issue['severity'] == 'medium') for r in reports_data)
        low_issues = sum(sum(1 for issue in r['issues'] if issue['severity'] == 'low') for r in reports_data)
        auto_fixable = sum(sum(1 for issue in r['issues'] if issue['auto_fixable']) for r in reports_data)
        
        # Генерация HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Draw.io Quality Analysis Report</title>
    <style>{self.template_css}</style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>🔍 Draw.io Quality Report</h1>
            <p class="subtitle">Комплексный анализ качества Draw.io файлов PIK методологии</p>
            <p>Сгенерирован: {datetime.now().strftime('%d.%m.%Y в %H:%M')}</p>
        </div>
    </div>
    
    <div class="container main-content">
        <div class="executive-summary">
            <h2>📋 Executive Summary</h2>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{total_files}</div>
                    <div class="metric-label">Файлов проанализировано</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{avg_score:.1f}</div>
                    <div class="metric-label">Средний балл качества</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{total_issues}</div>
                    <div class="metric-label">Всего проблем найдено</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{auto_fixable}</div>
                    <div class="metric-label">Автоисправимых</div>
                </div>
            </div>
            
            <div class="quality-distribution">
                <h3>Распределение по качеству:</h3>
                <div>
                    <strong>Отличное качество (80-100 баллов):</strong> {excellent} файлов ({excellent/total_files*100:.1f}%)
                    <div class="quality-bar">
                        <div class="quality-fill quality-excellent" style="width: {excellent/total_files*100:.1f}%"></div>
                    </div>
                </div>
                <div>
                    <strong>Хорошее качество (60-79 баллов):</strong> {good} файлов ({good/total_files*100:.1f}%)
                    <div class="quality-bar">
                        <div class="quality-fill quality-good" style="width: {good/total_files*100:.1f}%"></div>
                    </div>
                </div>
                <div>
                    <strong>Требует улучшения (<60 баллов):</strong> {poor} файлов ({poor/total_files*100:.1f}%)
                    <div class="quality-bar">
                        <div class="quality-fill quality-poor" style="width: {poor/total_files*100:.1f}%"></div>
                    </div>
                </div>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card" style="background: linear-gradient(135deg, #f56565, #e53e3e);">
                    <div class="metric-value">{critical_issues}</div>
                    <div class="metric-label">Критических проблем</div>
                </div>
                <div class="metric-card" style="background: linear-gradient(135deg, #ed8936, #dd6b20);">
                    <div class="metric-value">{high_issues}</div>
                    <div class="metric-label">Высокоприоритетных</div>
                </div>
                <div class="metric-card" style="background: linear-gradient(135deg, #3182ce, #2c5282);">
                    <div class="metric-value">{medium_issues}</div>
                    <div class="metric-label">Средней важности</div>
                </div>
                <div class="metric-card" style="background: linear-gradient(135deg, #48bb78, #38a169);">
                    <div class="metric-value">{low_issues}</div>
                    <div class="metric-label">Низкоприоритетных</div>
                </div>
            </div>
        </div>
        
        <div class="file-reports">
"""
        
        # Сортируем отчеты по баллу (лучшие сначала)
        sorted_reports = sorted(reports_data, key=lambda x: x['overall_score'], reverse=True)
        
        for report in sorted_reports:
            score_class = self._get_score_class(report['overall_score'])
            
            html_content += f"""
            <div class="file-card">
                <div class="file-header">
                    <div class="file-title">{report['filename']}</div>
                    <div class="score-badge score-{score_class}">{report['overall_score']:.0f}/100</div>
                </div>
                <div class="file-content">
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-value">{report['stats'].get('file_size', 0) // 1024}</div>
                            <div class="stat-label">KB</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{report['stats'].get('cell_count', 0)}</div>
                            <div class="stat-label">Элементов</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{report['performance_metrics'].get('metrics', {}).get('parse_time_seconds', 'N/A')}</div>
                            <div class="stat-label">Сек парсинг</div>
                        </div>
                    </div>
                    
                    <div class="test-results">
                        <div class="test-category">
                            <h4>🔧 Backend тесты</h4>
                            <div class="test-badges">
                                {self._render_test_badges(report.get('backend_tests', {}).get('tests', {}))}
                            </div>
                        </div>
                        <div class="test-category">
                            <h4>🎨 Frontend тесты</h4>
                            <div class="test-badges">
                                {self._render_test_badges(report.get('frontend_tests', {}).get('tests', {}))}
                            </div>
                        </div>
                    </div>
                    
                    {self._render_issues_section(report['issues'])}
                </div>
            </div>
"""
        
        # Рекомендации
        recommendations = self._generate_recommendations(avg_score, critical_issues, high_issues, auto_fixable)
        
        html_content += f"""
        </div>
        
        <div class="recommendations">
            <h3>💡 Рекомендации по улучшению</h3>
            <ul>
                {recommendations}
            </ul>
        </div>
    </div>
    
    <div class="footer">
        <p>Отчет сгенерирован автоматически системой Draw.io Quality Tester</p>
        <p>PIK Platform Innovation Kit - Digital Transformation Framework</p>
    </div>
    
    <script>
        // Анимация появления элементов
        document.addEventListener('DOMContentLoaded', function() {{
            const cards = document.querySelectorAll('.file-card');
            cards.forEach((card, index) => {{
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {{
                    card.style.transition = 'all 0.5s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }}, index * 100);
            }});
        }});
    </script>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 HTML отчет сохранен: {output_path}")
    
    def _get_score_class(self, score: float) -> str:
        """Определение CSS класса для балла"""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        else:
            return "poor"
    
    def _render_test_badges(self, tests: Dict) -> str:
        """Рендеринг бейджей тестов"""
        badges = []
        for test_name, result in tests.items():
            status = "passed" if result.get("passed", False) else "failed"
            badges.append(f'<span class="test-badge test-{status}">{test_name.replace("_", " ")}</span>')
        return ' '.join(badges)
    
    def _render_issues_section(self, issues: List[Dict]) -> str:
        """Рендеринг секции проблем"""
        if not issues:
            return '<div class="issues-section"><p style="color: #48bb78; font-weight: 500;">🎉 Проблем не найдено!</p></div>'
        
        # Группируем по серьезности
        issues_by_severity = {}
        for issue in issues:
            severity = issue['severity']
            if severity not in issues_by_severity:
                issues_by_severity[severity] = []
            issues_by_severity[severity].append(issue)
        
        html = '<div class="issues-section"><h4>⚠️ Найденные проблемы:</h4>'
        
        severity_order = ['critical', 'high', 'medium', 'low']
        severity_labels = {
            'critical': '🔴 Критические',
            'high': '🟠 Высокоприоритетные', 
            'medium': '🟡 Средней важности',
            'low': '🟢 Низкоприоритетные'
        }
        
        for severity in severity_order:
            if severity in issues_by_severity:
                html += f'<div class="issue-category"><h5>{severity_labels[severity]} ({len(issues_by_severity[severity])})</h5>'
                
                # Показываем только первые 3 проблемы каждой категории
                for issue in issues_by_severity[severity][:3]:
                    auto_fix = '<span class="auto-fix-badge">Автоисправимо</span>' if issue.get('auto_fixable') else ''
                    html += f"""
                    <div class="issue-item issue-{severity}">
                        <div class="issue-title">{issue['issue_type'].replace('_', ' ').title()}{auto_fix}</div>
                        <div class="issue-description">{issue['description']}</div>
                        <div class="issue-suggestion">💡 {issue['suggestion']}</div>
                    </div>
                    """
                
                if len(issues_by_severity[severity]) > 3:
                    html += f'<p style="color: #718096; font-size: 0.8rem; text-align: center; margin: 0.5rem 0;">... и еще {len(issues_by_severity[severity]) - 3} проблем этой категории</p>'
                
                html += '</div>'
        
        html += '</div>'
        return html
    
    def _generate_recommendations(self, avg_score: float, critical: int, high: int, auto_fixable: int) -> str:
        """Генерация рекомендаций"""
        recommendations = []
        
        if critical > 0:
            recommendations.append("Немедленно исправить критические проблемы - они могут полностью нарушить работу диаграмм")
        
        if high > 0:
            recommendations.append("Обратить внимание на высокоприоритетные проблемы, влияющие на качество визуализации")
        
        if auto_fixable > 0:
            recommendations.append(f"Использовать автоматическое исправление для {auto_fixable} проблем - это быстро и безопасно")
        
        if avg_score < 60:
            recommendations.append("Средний балл ниже приемлемого уровня - рекомендуется комплексная доработка файлов")
            recommendations.append("Рассмотреть возможность пересоздания диаграмм с учетом стандартов качества")
        elif avg_score < 80:
            recommendations.append("Есть хороший потенциал для улучшения - сосредоточиться на проблемах средней важности")
        
        recommendations.append("Регулярно проводить тестирование качества при обновлении диаграмм")
        recommendations.append("Использовать стандартные шаблоны и стили для обеспечения консистентности")
        
        return ''.join(f'<li>{rec}</li>' for rec in recommendations)


def main():
    """Генерация HTML отчета из JSON"""
    generator = HTMLReportGenerator()
    
    json_file = "drawio_quality_report.json"
    if not os.path.exists(json_file):
        print(f"❌ Файл {json_file} не найден. Сначала запустите тестирование качества.")
        return
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            reports_data = json.load(f)
        
        output_file = "drawio_quality_report.html"
        generator.generate_html_report(reports_data, output_file)
        
        print(f"✅ HTML отчет создан: {output_file}")
        print(f"🌐 Откройте в браузере: file://{os.path.abspath(output_file)}")
        
    except Exception as e:
        print(f"❌ Ошибка генерации отчета: {e}")

if __name__ == "__main__":
    main()
