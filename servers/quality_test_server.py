#!/usr/bin/env python3
"""
Draw.io Quality Test Web Interface
==================================

Веб-интерфейс для управления тестированием качества Draw.io файлов
"""

from flask import Flask, render_template_string, jsonify, request, send_file
import os
import json
from drawio_quality_tester import DrawIOQualityTester, DrawIOQualityReport
import threading
import time
from datetime import datetime

app = Flask(__name__)
quality_tester = DrawIOQualityTester()

# Глобальное хранилище результатов тестирования
test_results = {}
test_status = {"running": False, "progress": 0, "current_file": ""}

@app.route('/')
def quality_dashboard():
    """Главная страница дашборда качества"""
    return render_template_string("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Draw.io Quality Tester</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8f9fa; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem 0; }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        .header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .header p { font-size: 1.1rem; opacity: 0.9; }
        .main-content { padding: 2rem 0; }
        .test-controls { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 2rem; }
        .btn { padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; transition: all 0.3s; }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5a6fd8; transform: translateY(-2px); }
        .btn-success { background: #51cf66; color: white; }
        .btn-success:hover { background: #47c05f; }
        .btn-danger { background: #ff6b6b; color: white; }
        .btn-danger:hover { background: #ff5252; }
        .btn:disabled { background: #adb5bd; cursor: not-allowed; transform: none; }
        .progress-bar { width: 100%; height: 8px; background: #e9ecef; border-radius: 4px; margin: 1rem 0; overflow: hidden; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); transition: width 0.3s; }
        .status-text { color: #6c757d; font-size: 0.9rem; }
        .results-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 1.5rem; margin-top: 2rem; }
        .result-card { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.3s; }
        .result-card:hover { transform: translateY(-4px); }
        .card-header { padding: 1rem 1.5rem; background: #f8f9fa; border-bottom: 1px solid #dee2e6; display: flex; justify-content: space-between; align-items: center; }
        .card-body { padding: 1.5rem; }
        .score-circle { width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; font-weight: bold; margin: 0 auto 1rem; }
        .score-excellent { background: linear-gradient(135deg, #51cf66, #40c057); color: white; }
        .score-good { background: linear-gradient(135deg, #ffd43b, #fab005); color: white; }
        .score-poor { background: linear-gradient(135deg, #ff6b6b, #fa5252); color: white; }
        .stats-row { display: flex; justify-content: space-between; margin: 0.5rem 0; }
        .issue-badge { display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; margin: 2px; }
        .issue-critical { background: #ffebee; color: #c62828; }
        .issue-high { background: #fff3e0; color: #ef6c00; }
        .issue-medium { background: #e3f2fd; color: #1565c0; }
        .issue-low { background: #e8f5e9; color: #2e7d32; }
        .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .summary-card { background: white; padding: 1.5rem; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .summary-value { font-size: 2rem; font-weight: bold; color: #667eea; }
        .summary-label { color: #6c757d; margin-top: 0.5rem; }
        .action-buttons { display: flex; gap: 1rem; margin-top: 1rem; flex-wrap: wrap; }
        .loading { display: none; }
        .loading.active { display: block; }
        .hidden { display: none; }
        .file-actions { margin-top: 1rem; }
        .file-actions button { margin-right: 0.5rem; margin-bottom: 0.5rem; }
        .issues-list { margin-top: 1rem; max-height: 300px; overflow-y: auto; }
        .issue-item { padding: 0.5rem; border-left: 4px solid; margin: 0.5rem 0; border-radius: 4px; font-size: 0.9rem; }
        .test-categories { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0; }
        .test-category { background: #f8f9fa; padding: 1rem; border-radius: 8px; }
        .test-result { display: inline-block; padding: 2px 6px; border-radius: 12px; font-size: 0.75rem; margin: 1px; }
        .test-passed { background: #d4edda; color: #155724; }
        .test-failed { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>🔍 Draw.io Quality Tester</h1>
            <p>Комплексное тестирование качества Draw.io файлов PIK методологии</p>
        </div>
    </div>
    
    <div class="container main-content">
        <div class="test-controls">
            <h2>Управление тестированием</h2>
            <div class="action-buttons">
                <button class="btn btn-primary" id="start-test-btn" onclick="startQualityTest()">🚀 Запустить тестирование</button>
                <button class="btn btn-success" onclick="loadResults()">📊 Загрузить результаты</button>
                <button class="btn btn-danger" onclick="autoFixIssues()">🛠️ Автоисправление</button>
                <button class="btn btn-success" onclick="generateReport()">📄 Генерировать отчет</button>
            </div>
            
            <div id="progress-container" class="loading">
                <div class="progress-bar">
                    <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
                </div>
                <div class="status-text" id="status-text">Подготовка к тестированию...</div>
            </div>
        </div>
        
        <div id="summary-section" class="hidden">
            <div class="summary-cards" id="summary-cards">
                <!-- Карточки сводки будут добавлены динамически -->
            </div>
        </div>
        
        <div id="results-section" class="hidden">
            <h2>Результаты тестирования</h2>
            <div class="results-grid" id="results-grid">
                <!-- Результаты будут добавлены динамически -->
            </div>
        </div>
    </div>

    <script>
        let pollInterval = null;
        
        async function startQualityTest() {
            const btn = document.getElementById('start-test-btn');
            const progressContainer = document.getElementById('progress-container');
            
            btn.disabled = true;
            btn.textContent = '⏳ Тестирование...';
            progressContainer.classList.add('active');
            
            try {
                const response = await fetch('/api/start-test', {
                    method: 'POST'
                });
                
                if (response.ok) {
                    // Начинаем опрос статуса
                    pollInterval = setInterval(checkTestStatus, 1000);
                } else {
                    throw new Error('Ошибка запуска тестирования');
                }
            } catch (error) {
                alert('Ошибка: ' + error.message);
                btn.disabled = false;
                btn.textContent = '🚀 Запустить тестирование';
                progressContainer.classList.remove('active');
            }
        }
        
        async function checkTestStatus() {
            try {
                const response = await fetch('/api/test-status');
                const status = await response.json();
                
                const progressFill = document.getElementById('progress-fill');
                const statusText = document.getElementById('status-text');
                
                progressFill.style.width = status.progress + '%';
                statusText.textContent = status.current_file || 'Обработка...';
                
                if (!status.running) {
                    // Тестирование завершено
                    clearInterval(pollInterval);
                    pollInterval = null;
                    
                    const btn = document.getElementById('start-test-btn');
                    btn.disabled = false;
                    btn.textContent = '🚀 Запустить тестирование';
                    
                    document.getElementById('progress-container').classList.remove('active');
                    
                    // Загружаем результаты
                    loadResults();
                }
            } catch (error) {
                console.error('Ошибка проверки статуса:', error);
            }
        }
        
        async function loadResults() {
            try {
                const response = await fetch('/api/results');
                const data = await response.json();
                
                if (data.reports && data.reports.length > 0) {
                    displaySummary(data.summary);
                    displayResults(data.reports);
                    
                    document.getElementById('summary-section').classList.remove('hidden');
                    document.getElementById('results-section').classList.remove('hidden');
                } else {
                    alert('Нет результатов для отображения. Запустите тестирование.');
                }
            } catch (error) {
                alert('Ошибка загрузки результатов: ' + error.message);
            }
        }
        
        function displaySummary(summary) {
            const container = document.getElementById('summary-cards');
            container.innerHTML = `
                <div class="summary-card">
                    <div class="summary-value">${summary.total_files}</div>
                    <div class="summary-label">Файлов протестировано</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">${summary.avg_score.toFixed(1)}</div>
                    <div class="summary-label">Средний балл</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">${summary.total_issues}</div>
                    <div class="summary-label">Всего проблем</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">${summary.critical_issues}</div>
                    <div class="summary-label">Критических</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">${summary.auto_fixable}</div>
                    <div class="summary-label">Автоисправимых</div>
                </div>
            `;
        }
        
        function displayResults(reports) {
            const container = document.getElementById('results-grid');
            container.innerHTML = '';
            
            reports.forEach(report => {
                const scoreClass = report.overall_score >= 80 ? 'excellent' : 
                                 report.overall_score >= 60 ? 'good' : 'poor';
                
                const issuesByCategory = {};
                report.issues.forEach(issue => {
                    if (!issuesByCategory[issue.severity]) {
                        issuesByCategory[issue.severity] = 0;
                    }
                    issuesByCategory[issue.severity]++;
                });
                
                const issuesList = report.issues.slice(0, 5).map(issue => `
                    <div class="issue-item issue-${issue.severity}">
                        <strong>${issue.issue_type.replace(/_/g, ' ')}</strong>: ${issue.description}
                    </div>
                `).join('');
                
                const testResults = generateTestResults(report);
                
                const card = document.createElement('div');
                card.className = 'result-card';
                card.innerHTML = `
                    <div class="card-header">
                        <h3>${report.filename}</h3>
                        <small>${report.test_timestamp}</small>
                    </div>
                    <div class="card-body">
                        <div class="score-circle score-${scoreClass}">
                            ${report.overall_score.toFixed(0)}
                        </div>
                        
                        <div class="stats-row">
                            <span>Размер файла:</span>
                            <span>${(report.stats.file_size / 1024).toFixed(1)} KB</span>
                        </div>
                        <div class="stats-row">
                            <span>Элементов:</span>
                            <span>${report.stats.cell_count || 0}</span>
                        </div>
                        <div class="stats-row">
                            <span>Время парсинга:</span>
                            <span>${report.performance_metrics.metrics?.parse_time_seconds || 'N/A'} сек</span>
                        </div>
                        
                        <div style="margin: 1rem 0;">
                            ${Object.entries(issuesByCategory).map(([severity, count]) => 
                                `<span class="issue-badge issue-${severity}">${severity}: ${count}</span>`
                            ).join('')}
                        </div>
                        
                        ${testResults}
                        
                        <div class="file-actions">
                            <button class="btn btn-primary" onclick="viewDetails('${report.filename}')">📋 Детали</button>
                            <button class="btn btn-danger" onclick="fixFile('${report.filename}')">🔧 Исправить</button>
                        </div>
                        
                        <div class="issues-list">
                            ${issuesList}
                            ${report.issues.length > 5 ? `<div style="text-align: center; color: #6c757d; font-size: 0.8rem;">... и еще ${report.issues.length - 5} проблем</div>` : ''}
                        </div>
                    </div>
                `;
                
                container.appendChild(card);
            });
        }
        
        function generateTestResults(report) {
            const categories = [
                { name: 'Backend', tests: report.backend_tests.tests },
                { name: 'Frontend', tests: report.frontend_tests.tests }
            ];
            
            return `
                <div class="test-categories">
                    ${categories.map(category => `
                        <div class="test-category">
                            <h5>${category.name}</h5>
                            ${Object.entries(category.tests).map(([testName, result]) => 
                                `<span class="test-result test-${result.passed ? 'passed' : 'failed'}">${testName}</span>`
                            ).join('')}
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        async function autoFixIssues() {
            if (!confirm('Применить автоматические исправления ко всем файлам?')) {
                return;
            }
            
            try {
                const response = await fetch('/api/auto-fix', {
                    method: 'POST'
                });
                
                const result = await response.json();
                alert(`Исправления применены: ${result.total_fixes} проблем исправлено в ${result.files_fixed} файлах`);
                
                // Перезагружаем результаты
                loadResults();
            } catch (error) {
                alert('Ошибка автоисправления: ' + error.message);
            }
        }
        
        async function fixFile(filename) {
            if (!confirm(`Применить автоисправления к файлу ${filename}?`)) {
                return;
            }
            
            try {
                const response = await fetch('/api/fix-file', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({filename: filename})
                });
                
                const result = await response.json();
                alert(`Файл ${filename}: исправлено ${result.fixes_applied} проблем`);
                
                // Перезагружаем результаты
                loadResults();
            } catch (error) {
                alert('Ошибка исправления файла: ' + error.message);
            }
        }
        
        async function generateReport() {
            try {
                const response = await fetch('/api/generate-report', {
                    method: 'POST'
                });
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'drawio_quality_report.html';
                    a.click();
                    window.URL.revokeObjectURL(url);
                } else {
                    throw new Error('Ошибка генерации отчета');
                }
            } catch (error) {
                alert('Ошибка генерации отчета: ' + error.message);
            }
        }
        
        function viewDetails(filename) {
            // Открываем детальный просмотр (можно реализовать модальное окно)
            alert(`Детальный просмотр для ${filename} - функция в разработке`);
        }
        
        // Автозагрузка результатов при открытии страницы
        document.addEventListener('DOMContentLoaded', function() {
            loadResults();
        });
    </script>
</body>
</html>
""")

@app.route('/api/start-test', methods=['POST'])
def start_test():
    """Запуск тестирования качества"""
    global test_status
    
    if test_status["running"]:
        return jsonify({"error": "Тестирование уже запущено"}), 400
    
    def run_test():
        global test_status, test_results
        
        test_status["running"] = True
        test_status["progress"] = 0
        
        try:
            drawio_dir = "./output/drawio"
            if not os.path.exists(drawio_dir):
                test_status["running"] = False
                return
            
            reports = quality_tester.run_batch_test(drawio_dir)
            
            # Подсчитываем статистику
            total_issues = sum(len(r.issues) for r in reports)
            critical_issues = sum(sum(1 for issue in r.issues if issue.severity == 'critical') for r in reports)
            auto_fixable = sum(sum(1 for issue in r.issues if issue.auto_fixable) for r in reports)
            avg_score = sum(r.overall_score for r in reports) / len(reports) if reports else 0
            
            test_results = {
                "reports": reports,
                "summary": {
                    "total_files": len(reports),
                    "avg_score": avg_score,
                    "total_issues": total_issues,
                    "critical_issues": critical_issues,
                    "auto_fixable": auto_fixable,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            test_status["progress"] = 100
            
        except Exception as e:
            print(f"Ошибка тестирования: {e}")
        finally:
            test_status["running"] = False
    
    thread = threading.Thread(target=run_test)
    thread.start()
    
    return jsonify({"status": "started"})

@app.route('/api/test-status')
def get_test_status():
    """Получение статуса тестирования"""
    return jsonify(test_status)

@app.route('/api/results')
def get_results():
    """Получение результатов тестирования"""
    if not test_results:
        return jsonify({"reports": [], "summary": {}})
    
    # Конвертируем dataclass в dict для JSON
    serializable_reports = []
    for report in test_results["reports"]:
        report_dict = {
            "filename": report.filename,
            "overall_score": report.overall_score,
            "issues": [
                {
                    "severity": issue.severity,
                    "category": issue.category,
                    "issue_type": issue.issue_type,
                    "description": issue.description,
                    "location": issue.location,
                    "suggestion": issue.suggestion,
                    "auto_fixable": issue.auto_fixable
                }
                for issue in report.issues
            ],
            "stats": report.stats,
            "backend_tests": report.backend_tests,
            "frontend_tests": report.frontend_tests,
            "performance_metrics": report.performance_metrics,
            "test_timestamp": report.test_timestamp
        }
        serializable_reports.append(report_dict)
    
    return jsonify({
        "reports": serializable_reports,
        "summary": test_results["summary"]
    })

@app.route('/api/auto-fix', methods=['POST'])
def auto_fix_all():
    """Автоисправление всех файлов"""
    if not test_results:
        return jsonify({"error": "Нет результатов тестирования"}), 400
    
    total_fixes = 0
    files_fixed = 0
    
    drawio_dir = "./output/drawio"
    
    for report in test_results["reports"]:
        file_path = os.path.join(drawio_dir, report.filename)
        if os.path.exists(file_path):
            result = quality_tester.auto_fix_issues(file_path)
            if result["success"] and result["fixes_applied"] > 0:
                total_fixes += result["fixes_applied"]
                files_fixed += 1
    
    return jsonify({
        "total_fixes": total_fixes,
        "files_fixed": files_fixed
    })

@app.route('/api/fix-file', methods=['POST'])
def fix_single_file():
    """Исправление конкретного файла"""
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename:
        return jsonify({"error": "Не указан файл"}), 400
    
    drawio_dir = "./output/drawio"
    file_path = os.path.join(drawio_dir, filename)
    
    if not os.path.exists(file_path):
        return jsonify({"error": "Файл не найден"}), 404
    
    result = quality_tester.auto_fix_issues(file_path)
    return jsonify(result)

@app.route('/api/generate-report', methods=['POST'])
def generate_html_report():
    """Генерация HTML отчета"""
    if not test_results:
        return jsonify({"error": "Нет результатов тестирования"}), 400
    
    report_path = "drawio_quality_report.html"
    quality_tester.generate_html_report(test_results["reports"], report_path)
    
    return send_file(report_path, as_attachment=True)

def main():
    """Запуск веб-сервера"""
    print("🚀 Запуск Draw.io Quality Test Server...")
    print("🌐 Веб-интерфейс: http://localhost:8002")
    
    app.run(host='0.0.0.0', port=8002, debug=True)

if __name__ == "__main__":
    main()
