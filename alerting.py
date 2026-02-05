# -*- coding: utf-8 -*-
"""
预警与报告模块
实现PRD中的预警与报告功能 (Alerting & Reporting)
"""
import smtplib
import json
import os
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import pandas as pd
from typing import Dict, List, Any, Optional
import requests
import logging

from ai_analysis import PolicyAnalyzer, PolicyTrendAnalyzer

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertingConfig:
    """预警配置类"""
    
    def __init__(self):
        self.config_file = "alerting_config.json"
        self.default_config = {
            "alert_threshold": 8.0,
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "recipients": []
            },
            "slack": {
                "enabled": False,
                "webhook_url": "",
                "channel": "#policy-alerts"
            },
            "alert_frequency": "daily",  # daily, weekly, immediate
            "domains_to_monitor": [
                "隐私保护", "算法透明度", "未成年人保护", 
                "生成式AI", "数据安全", "内容安全"
            ],
            "departments_to_monitor": [
                "国家网信办", "工信部", "全国信息安全标准化技术委员会"
            ]
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载配置失败: {e}, 使用默认配置")
        
        return self.default_config.copy()
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def update_config(self, new_config: Dict):
        """更新配置"""
        self.config.update(new_config)
        self.save_config()

class PolicyAlerter:
    """政策预警器"""
    
    def __init__(self, config_file: str = None):
        self.config = AlertingConfig()
        self.policy_analyzer = PolicyAnalyzer()
        self.trend_analyzer = PolicyTrendAnalyzer()
        
        # 创建输出目录
        self.output_dir = "alerts_output"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def check_high_risk_policies(self, policies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检查高风险政策"""
        threshold = self.config.config.get("alert_threshold", 8.0)
        high_risk_policies = self.trend_analyzer.generate_risk_alerts(policies, threshold)
        
        # 额外过滤：只关注特定部门和领域
        monitored_departments = self.config.config.get("departments_to_monitor", [])
        monitored_domains = self.config.config.get("domains_to_monitor", [])
        
        filtered_alerts = []
        for alert in high_risk_policies:
            # 部门过滤
            if monitored_departments and alert.get('department') not in monitored_departments:
                continue
            
            # 领域过滤
            if monitored_domains:
                alert_domains = alert.get('affected_domains', [])
                if not any(domain in monitored_domains for domain in alert_domains):
                    continue
            
            filtered_alerts.append(alert)
        
        return filtered_alerts
    
    def generate_alert_report(self, alerts: List[Dict[str, Any]]) -> str:
        """生成预警报告"""
        if not alerts:
            return "当前没有高风险政策预警。"
        
        report_lines = [
            "🚨 AI政策风险预警报告",
            f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"⚡ 预警数量: {len(alerts)}",
            "=" * 50
        ]
        
        for i, alert in enumerate(alerts, 1):
            report_lines.extend([
                f"\n📋 预警 {i}: {alert['title']}",
                f"🏛️  发布部门: {alert['department']}",
                f"📅 发布日期: {alert['publication_date']}",
                f"⭐ 监管评分: {alert['regulatory_score']:.1f}/10",
                f"🎯 涉及领域: {', '.join(alert['affected_domains'])}",
                f"⚠️  风险因素: {', '.join(alert['risk_factors'])}",
                f"🔗 链接: {alert['url']}",
                "-" * 40
            ])
        
        report_lines.extend([
            "\n💡 建议行动:",
            "1. 评估政策对现有业务的影响",
            "2. 与法务部门确认合规要求", 
            "3. 制定相应的应对措施",
            "4. 持续监控政策实施细则"
        ])
        
        return '\n'.join(report_lines)
    
    def send_email_alert(self, alert_report: str, alerts: List[Dict[str, Any]]):
        """发送邮件预警"""
        email_config = self.config.config.get("email", {})
        
        if not email_config.get("enabled", False):
            logger.info("邮件预警已禁用")
            return False
        
        if not email_config.get("recipients"):
            logger.warning("未配置邮件接收者")
            return False
        
        try:
            # 创建邮件
            msg = MimeMultipart()
            msg['From'] = email_config.get("username", "")
            msg['To'] = ", ".join(email_config.get("recipients", []))
            msg['Subject'] = f"AI政策风险预警 - {len(alerts)}个高风险政策 ({datetime.now().strftime('%Y-%m-%d')})"
            
            # 添加正文
            msg.attach(MimeText(alert_report, 'plain', 'utf-8'))
            
            # 连接SMTP服务器并发送
            server = smtplib.SMTP(email_config.get("smtp_server", ""), 
                                email_config.get("smtp_port", 587))
            server.starttls()
            server.login(email_config.get("username", ""), 
                        email_config.get("password", ""))
            
            text = msg.as_string()
            server.sendmail(email_config.get("username", ""), 
                          email_config.get("recipients", []), text)
            server.quit()
            
            logger.info(f"邮件预警已发送至 {len(email_config.get('recipients', []))} 个接收者")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件预警失败: {e}")
            return False
    
    def send_slack_alert(self, alert_report: str, alerts: List[Dict[str, Any]]):
        """发送Slack预警"""
        slack_config = self.config.config.get("slack", {})
        
        if not slack_config.get("enabled", False):
            logger.info("Slack预警已禁用")
            return False
        
        webhook_url = slack_config.get("webhook_url", "")
        if not webhook_url:
            logger.warning("未配置Slack Webhook URL")
            return False
        
        try:
            # 构建Slack消息
            slack_message = {
                "text": f"🚨 AI政策风险预警 ({len(alerts)}个高风险政策)",
                "channel": slack_config.get("channel", "#policy-alerts"),
                "attachments": [
                    {
                        "color": "danger" if len(alerts) > 0 else "good",
                        "fields": [
                            {
                                "title": "预警时间",
                                "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                "short": True
                            },
                            {
                                "title": "预警数量", 
                                "value": str(len(alerts)),
                                "short": True
                            }
                        ]
                    }
                ]
            }
            
            # 添加前3个预警的详细信息
            for i, alert in enumerate(alerts[:3], 1):
                slack_message["attachments"].append({
                    "title": f"预警 {i}: {alert['title'][:50]}...",
                    "text": f"部门: {alert['department']} | 评分: {alert['regulatory_score']:.1f}/10",
                    "color": "warning"
                })
            
            # 发送到Slack
            response = requests.post(webhook_url, json=slack_message, timeout=10)
            response.raise_for_status()
            
            logger.info("Slack预警已发送")
            return True
            
        except Exception as e:
            logger.error(f"发送Slack预警失败: {e}")
            return False
    
    def save_alert_log(self, alerts: List[Dict[str, Any]], alert_report: str):
        """保存预警日志"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存详细的预警数据
        alert_file = os.path.join(self.output_dir, f"alerts_{timestamp}.json")
        with open(alert_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "alert_count": len(alerts),
                "threshold": self.config.config.get("alert_threshold", 8.0),
                "alerts": alerts
            }, f, ensure_ascii=False, indent=2)
        
        # 保存报告文本
        report_file = os.path.join(self.output_dir, f"alert_report_{timestamp}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(alert_report)
        
        logger.info(f"预警日志已保存: {alert_file}, {report_file}")
        return alert_file, report_file
    
    def run_alert_check(self, policies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行预警检查"""
        logger.info("开始执行政策风险预警检查...")
        
        # 检查高风险政策
        alerts = self.check_high_risk_policies(policies)
        
        # 生成报告
        alert_report = self.generate_alert_report(alerts)
        
        # 保存日志
        log_files = self.save_alert_log(alerts, alert_report)
        
        # 发送通知
        notification_results = {
            "email_sent": False,
            "slack_sent": False
        }
        
        if alerts:  # 只有在有预警时才发送通知
            notification_results["email_sent"] = self.send_email_alert(alert_report, alerts)
            notification_results["slack_sent"] = self.send_slack_alert(alert_report, alerts)
        
        result = {
            "alert_count": len(alerts),
            "alerts": alerts,
            "report": alert_report,
            "log_files": log_files,
            "notifications": notification_results,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"预警检查完成，发现 {len(alerts)} 个高风险政策")
        return result

class AlertScheduler:
    """预警调度器"""
    
    def __init__(self):
        self.alerter = PolicyAlerter()
        self.last_check_file = "last_alert_check.json"
    
    def should_run_check(self) -> bool:
        """判断是否应该执行检查"""
        frequency = self.alerter.config.config.get("alert_frequency", "daily")
        
        if not os.path.exists(self.last_check_file):
            return True
        
        try:
            with open(self.last_check_file, 'r') as f:
                last_check_data = json.load(f)
                last_check_time = datetime.fromisoformat(last_check_data["timestamp"])
        except:
            return True
        
        now = datetime.now()
        
        if frequency == "immediate":
            return True
        elif frequency == "daily":
            return (now - last_check_time).days >= 1
        elif frequency == "weekly":
            return (now - last_check_time).days >= 7
        
        return False
    
    def update_last_check(self):
        """更新最后检查时间"""
        try:
            with open(self.last_check_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat()
                }, f)
        except Exception as e:
            logger.error(f"更新检查时间失败: {e}")
    
    def run_scheduled_check(self, csv_files: List[str]):
        """执行定时检查"""
        if not self.should_run_check():
            logger.info("未到检查时间，跳过预警检查")
            return
        
        # 加载政策数据
        all_policies = []
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                try:
                    df = pd.read_csv(csv_file)
                    policies = df.to_dict('records')
                    all_policies.extend(policies)
                except Exception as e:
                    logger.error(f"加载政策数据失败 {csv_file}: {e}")
        
        if not all_policies:
            logger.warning("没有找到政策数据，跳过预警检查")
            return
        
        # 执行预警检查
        result = self.alerter.run_alert_check(all_policies)
        
        # 更新检查时间
        self.update_last_check()
        
        return result

def main():
    """主函数 - 示例用法"""
    print("=" * 60)
    print("AI政策预警系统 v1.0")
    print("=" * 60)
    
    # 创建预警器
    alerter = PolicyAlerter()
    
    # 查找现有的政策数据
    csv_files = ['miit_policies.csv', 'cac_policies.csv', 'tc260_policies.csv']
    existing_files = [f for f in csv_files if os.path.exists(f)]
    
    if not existing_files:
        print("未找到政策数据文件，请先运行爬虫生成数据")
        return
    
    # 加载政策数据进行测试
    all_policies = []
    for csv_file in existing_files:
        df = pd.read_csv(csv_file)
        policies = df.to_dict('records')
        all_policies.extend(policies)
        print(f"已加载: {csv_file} ({len(policies)} 条记录)")
    
    # 执行预警检查
    result = alerter.run_alert_check(all_policies)
    
    print(f"\n预警检查结果:")
    print(f"  发现高风险政策: {result['alert_count']} 个")
    print(f"  邮件发送: {'成功' if result['notifications']['email_sent'] else '未启用/失败'}")
    print(f"  Slack发送: {'成功' if result['notifications']['slack_sent'] else '未启用/失败'}")
    
    # 显示预警报告
    if result['alert_count'] > 0:
        print("\n" + "="*50)
        print(result['report'])

if __name__ == "__main__":
    main()