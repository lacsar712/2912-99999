"""
生产线监控系统 - 测试执行脚本
运行所有测试并生成报告
"""
import sys
import os
import time
import subprocess
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.report_dir = os.path.join(self.test_dir, 'reports')
        self.results = []
        
        # 创建报告目录
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)
    
    def run_test_file(self, test_file, test_type):
        """运行单个测试文件"""
        print(f"\n{'='*60}")
        print(f"运行 {test_type}: {test_file}")
        print('='*60)
        
        test_path = os.path.join(self.test_dir, test_file)
        
        if not os.path.exists(test_path):
            print(f"⚠ 测试文件不存在: {test_path}")
            return None
        
        start_time = time.time()
        
        try:
            # 运行pytest
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', test_path, '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            elapsed_time = time.time() - start_time
            
            # 解析结果
            output = result.stdout + result.stderr
            
            # 统计测试数量
            passed = output.count(' PASSED ')
            failed = output.count(' FAILED ')
            error = output.count(' ERROR ')
            skipped = output.count(' SKIPPED ')
            
            result_data = {
                'type': test_type,
                'file': test_file,
                'passed': passed,
                'failed': failed,
                'error': error,
                'skipped': skipped,
                'total': passed + failed + error + skipped,
                'time': elapsed_time,
                'returncode': result.returncode,
                'output': output
            }
            
            status = '✅ 通过' if result.returncode == 0 else '❌ 失败'
            print(f"{status} - 通过: {passed}, 失败: {failed}, 错误: {error}, 跳过: {skipped}, 耗时: {elapsed_time:.2f}s")
            
            return result_data
            
        except subprocess.TimeoutExpired:
            print(f"❌ 超时 - 测试运行超过5分钟")
            return {
                'type': test_type,
                'file': test_file,
                'passed': 0,
                'failed': 0,
                'error': 1,
                'skipped': 0,
                'total': 1,
                'time': 300,
                'returncode': -1,
                'output': '测试超时'
            }
        except Exception as e:
            print(f"❌ 异常 - {str(e)}")
            return {
                'type': test_type,
                'file': test_file,
                'passed': 0,
                'failed': 0,
                'error': 1,
                'skipped': 0,
                'total': 1,
                'time': 0,
                'returncode': -1,
                'output': str(e)
            }
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("智能生产线监控系统 - 自动化测试")
        print("="*60)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # 定义测试文件
        test_files = [
            ('test_unit.py', '单元测试-工具类'),
            ('test_models.py', '单元测试-模型层'),
            ('test_services.py', '单元测试-服务层'),
            ('test_integration.py', '集成测试'),
            ('test_api_production.py', 'API测试-生产线'),
            ('test_functional.py', '功能测试'),
            ('test_security.py', '安全测试'),
        ]
        
        start_time = time.time()
        
        # 运行每个测试文件
        for test_file, test_type in test_files:
            result = self.run_test_file(test_file, test_type)
            if result:
                self.results.append(result)
        
        total_time = time.time() - start_time
        
        # 生成报告
        self.generate_report(total_time)
        
        return self.results
    
    def generate_report(self, total_time):
        """生成测试报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(self.report_dir, f'test_report_{timestamp}.md')
        
        # 统计汇总
        total_passed = sum(r['passed'] for r in self.results)
        total_failed = sum(r['failed'] for r in self.results)
        total_error = sum(r['error'] for r in self.results)
        total_skipped = sum(r['skipped'] for r in self.results)
        total_tests = sum(r['total'] for r in self.results)
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        report_content = f"""# 测试报告

## 执行摘要

| 项目 | 数值 |
|------|------|
| 执行时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| 总耗时 | {total_time:.2f} 秒 |
| 测试文件数 | {len(self.results)} |
| 总用例数 | {total_tests} |
| 通过 | {total_passed} ({success_rate:.1f}%) |
| 失败 | {total_failed} |
| 错误 | {total_error} |
| 跳过 | {total_skipped} |

## 详细结果

| 测试类型 | 文件 | 总计 | 通过 | 失败 | 错误 | 跳过 | 耗时 | 状态 |
|----------|------|------|------|------|------|------|------|------|
"""
        
        for result in self.results:
            status_icon = '✅' if result['returncode'] == 0 else '❌'
            report_content += f"| {result['type']} | {result['file']} | {result['total']} | {result['passed']} | {result['failed']} | {result['error']} | {result['skipped']} | {result['time']:.2f}s | {status_icon} |\n"
        
        report_content += """
## 结论

"""
        
        if total_failed == 0 and total_error == 0:
            report_content += "✅ **所有测试通过，系统功能正常。**\n"
        else:
            report_content += f"⚠️ **发现 {total_failed} 个失败和 {total_error} 个错误，需要修复。**\n"
        
        report_content += """
## 详细输出

"""
        
        for result in self.results:
            report_content += f"""
### {result['type']} - {result['file']}

```
{result['output'][:2000]}  # 限制输出长度
```

"""
        
        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n{'='*60}")
        print("测试执行完成")
        print('='*60)
        print(f"总用例: {total_tests}")
        print(f"通过: {total_passed} ({success_rate:.1f}%)")
        print(f"失败: {total_failed}")
        print(f"错误: {total_error}")
        print(f"跳过: {total_skipped}")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"报告已保存: {report_file}")
        print('='*60)


def main():
    """主函数"""
    runner = TestRunner()
    runner.run_all_tests()


if __name__ == '__main__':
    main()
