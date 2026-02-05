# -*- coding: utf-8 -*-
"""
AI政策分析与量化模块
实现PRD中的AI分析与量化功能 (Analytics & Quantification)
"""
import re
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolicyAnalyzer:
    """政策分析器 - 实现LLM风格的多维度结构化标注"""
    
    def __init__(self):
        # 监管态度关键词 (1-10评分)
        self.strict_keywords = {
            # 极度严格 (9-10分)
            "严禁": 10, "禁止": 9, "不得": 8, "违法": 10, "处罚": 9,
            "停业": 10, "吊销": 10, "责令": 8, "查处": 9, "整改": 7,
            
            # 高度监管 (7-8分)  
            "监管": 7, "合规": 7, "审查": 8, "审批": 7, "备案": 6,
            "许可": 7, "资质": 6, "认证": 6, "检查": 7, "督查": 8,
            
            # 中等管控 (5-6分)
            "规范": 5, "管理": 5, "制度": 5, "标准": 5, "要求": 4,
            "应当": 5, "必须": 6, "义务": 6, "责任": 5, "风险": 6,
            
            # 轻度引导 (3-4分)
            "指导": 3, "建议": 3, "推荐": 2, "提倡": 2, "倡导": 2,
        }
        
        self.innovation_keywords = {
            # 高度鼓励 (1-2分 - 低监管态度)
            "鼓励": 1, "支持": 1, "促进": 1, "推动": 2, "加快": 2,
            "创新": 1, "突破": 1, "发展": 2, "提升": 2, "优化": 2,
            
            # 中度推进 (2-3分)
            "应用": 2, "试点": 3, "示范": 3, "推广": 2, "普及": 2,
            "数字化": 2, "智能化": 1, "升级": 2, "转型": 2, "赋能": 1,
        }
        
        # 涉及领域关键词
        self.domain_keywords = {
            "隐私保护": ["隐私", "个人信息", "数据保护", "信息保护", "敏感信息"],
            "算法透明度": ["算法", "算法透明", "可解释", "黑盒", "算法歧视", "算法公平"],
            "未成年人保护": ["未成年", "儿童", "青少年", "学生", "未成年人保护"],
            "生成式AI": ["生成式", "大模型", "ChatGPT", "AIGC", "生成式人工智能", "深度合成"],
            "数据安全": ["数据安全", "网络安全", "信息安全", "数据泄露", "网络攻击"],
            "内容安全": ["内容安全", "有害信息", "虚假信息", "不良内容", "违法内容"]
        }
        
        # 强制程度关键词
        self.enforcement_levels = {
            "法律法规": ["法律", "法规", "条例", "刑法", "民法", "行政法"],
            "行政规章": ["规定", "办法", "细则", "规章", "管理办法", "实施细则"],
            "行业标准": ["标准", "规范", "指南", "准则", "技术标准", "国家标准"],
            "指导性文件": ["意见", "通知", "指导", "建议", "倡议", "指南"]
        }
        
    def calculate_regulatory_score(self, text: str) -> float:
        """
        计算监管态度评分 (1-10)
        1 = 极度鼓励创新, 10 = 极其严格限制
        """
        if not text:
            return 5.0
        
        text = text.lower()
        total_weight = 0
        weighted_score = 0
        
        # 计算严格监管词汇得分
        for keyword, score in self.strict_keywords.items():
            count = text.count(keyword)
            if count > 0:
                weight = min(count * 2, 10)  # 词频权重，上限10
                weighted_score += score * weight
                total_weight += weight
        
        # 计算创新鼓励词汇得分
        for keyword, score in self.innovation_keywords.items():
            count = text.count(keyword)
            if count > 0:
                weight = min(count * 1.5, 8)  # 创新词汇权重稍低
                weighted_score += score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 5.0  # 中性评分
        
        # 计算加权平均
        raw_score = weighted_score / total_weight
        
        # 归一化到1-10范围
        return max(1.0, min(10.0, raw_score))
    
    def identify_domains(self, text: str) -> List[str]:
        """识别涉及的领域"""
        if not text:
            return []
        
        text = text.lower()
        identified_domains = []
        
        for domain, keywords in self.domain_keywords.items():
            domain_score = sum(text.count(keyword.lower()) for keyword in keywords)
            if domain_score >= 1:  # 至少出现1次相关词汇
                identified_domains.append(domain)
        
        return identified_domains
    
    def determine_enforcement_level(self, text: str, title: str = "") -> str:
        """确定强制程度"""
        combined_text = f"{title} {text}".lower()
        
        level_scores = {}
        for level, keywords in self.enforcement_levels.items():
            score = sum(combined_text.count(keyword) for keyword in keywords)
            if score > 0:
                level_scores[level] = score
        
        if not level_scores:
            return "指导性文件"
        
        # 返回得分最高的类型
        return max(level_scores.items(), key=lambda x: x[1])[0]
    
    def analyze_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析单个政策的多维度信息"""
        title = policy_data.get('title', '')
        content = policy_data.get('full_text', '')
        combined_text = f"{title} {content}"
        
        analysis = {
            'regulatory_score': self.calculate_regulatory_score(combined_text),
            'identified_domains': self.identify_domains(combined_text),
            'enforcement_level': self.determine_enforcement_level(content, title),
            'content_length': len(content),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # 添加文本特征
        analysis['has_penalties'] = any(word in combined_text.lower() 
                                      for word in ['处罚', '罚款', '责任', '违法'])
        analysis['has_deadlines'] = bool(re.search(r'\d{4}年\d{1,2}月', combined_text))
        analysis['urgency_indicators'] = sum(combined_text.lower().count(word) 
                                           for word in ['紧急', '立即', '尽快', '马上'])
        
        return analysis

class PolicyTrendAnalyzer:
    """政策趋势分析器"""
    
    def __init__(self):
        self.policy_analyzer = PolicyAnalyzer()
    
    def analyze_temporal_trends(self, policies: List[Dict[str, Any]], 
                               time_window_months: int = 6) -> Dict[str, Any]:
        """分析时间趋势"""
        # 过滤有日期的政策
        dated_policies = [p for p in policies if p.get('publication_date')]
        
        if not dated_policies:
            return {"error": "没有足够的时间数据进行趋势分析"}
        
        # 按月分组
        monthly_data = {}
        for policy in dated_policies:
            try:
                date_str = policy['publication_date']
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                month_key = date_obj.strftime('%Y-%m')
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = []
                monthly_data[month_key].append(policy)
            except:
                continue
        
        # 计算每月的监管情绪
        monthly_sentiment = {}
        for month, month_policies in monthly_data.items():
            scores = []
            for policy in month_policies:
                analysis = self.policy_analyzer.analyze_policy(policy)
                scores.append(analysis['regulatory_score'])
            
            if scores:
                monthly_sentiment[month] = {
                    'avg_regulatory_score': np.mean(scores),
                    'policy_count': len(scores),
                    'max_score': max(scores),
                    'min_score': min(scores)
                }
        
        return {
            'monthly_sentiment': monthly_sentiment,
            'total_analyzed_policies': len(dated_policies),
            'date_range': {
                'earliest': min(p['publication_date'] for p in dated_policies),
                'latest': max(p['publication_date'] for p in dated_policies)
            }
        }
    
    def department_analysis(self, policies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """按部门分析政策分布"""
        dept_stats = {}
        
        for policy in policies:
            dept = policy.get('issuing_department', '未知部门')
            if dept not in dept_stats:
                dept_stats[dept] = {
                    'count': 0,
                    'regulatory_scores': [],
                    'domains': []
                }
            
            dept_stats[dept]['count'] += 1
            
            # 分析该政策
            analysis = self.policy_analyzer.analyze_policy(policy)
            dept_stats[dept]['regulatory_scores'].append(analysis['regulatory_score'])
            dept_stats[dept]['domains'].extend(analysis['identified_domains'])
        
        # 计算统计指标
        for dept, stats in dept_stats.items():
            if stats['regulatory_scores']:
                stats['avg_regulatory_score'] = np.mean(stats['regulatory_scores'])
                stats['regulatory_intensity'] = len([s for s in stats['regulatory_scores'] if s > 7])
            
            # 统计最常涉及的领域
            domain_counts = {}
            for domain in stats['domains']:
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            stats['top_domains'] = sorted(domain_counts.items(), 
                                        key=lambda x: x[1], reverse=True)[:3]
            
            # 清理临时数据
            del stats['regulatory_scores']
            del stats['domains']
        
        return dept_stats
    
    def generate_risk_alerts(self, policies: List[Dict[str, Any]], 
                           threshold: float = 8.0) -> List[Dict[str, Any]]:
        """生成风险预警"""
        alerts = []
        
        for policy in policies:
            analysis = self.policy_analyzer.analyze_policy(policy)
            
            if analysis['regulatory_score'] >= threshold:
                alert = {
                    'title': policy.get('title', 'N/A'),
                    'url': policy.get('url', ''),
                    'regulatory_score': analysis['regulatory_score'],
                    'department': policy.get('issuing_department', '未知'),
                    'publication_date': policy.get('publication_date', 'N/A'),
                    'risk_factors': [],
                    'affected_domains': analysis['identified_domains'],
                    'alert_timestamp': datetime.now().isoformat()
                }
                
                # 识别风险因素
                if analysis['has_penalties']:
                    alert['risk_factors'].append('包含处罚条款')
                if analysis['has_deadlines']:
                    alert['risk_factors'].append('设定时间期限')
                if analysis['urgency_indicators'] > 0:
                    alert['risk_factors'].append('存在紧急性指标')
                if analysis['enforcement_level'] in ['法律法规', '行政规章']:
                    alert['risk_factors'].append('强制执行级别高')
                
                alerts.append(alert)
        
        # 按监管分数排序
        alerts.sort(key=lambda x: x['regulatory_score'], reverse=True)
        return alerts

def main():
    """测试函数"""
    print("AI政策分析与量化模块测试")
    
    # 测试数据
    sample_policies = [
        {
            'title': '关于加强人工智能算法安全管理的规定',
            'full_text': '为规范人工智能算法应用，防范算法安全风险，保护用户权益，现制定本规定。算法提供者应当建立健全算法安全管理制度，不得利用算法从事危害国家安全的活动。',
            'publication_date': '2023-12-01',
            'issuing_department': '国家网信办'
        },
        {
            'title': '关于促进人工智能产业发展的指导意见',
            'full_text': '为促进人工智能产业健康发展，推动数字经济转型升级，鼓励创新应用，支持企业加快人工智能技术研发和产业化应用。',
            'publication_date': '2023-11-15',
            'issuing_department': '工信部'
        }
    ]
    
    # 初始化分析器
    analyzer = PolicyAnalyzer()
    trend_analyzer = PolicyTrendAnalyzer()
    
    # 测试单个政策分析
    print("\n=== 单个政策分析测试 ===")
    for i, policy in enumerate(sample_policies):
        print(f"\n政策 {i+1}: {policy['title']}")
        analysis = analyzer.analyze_policy(policy)
        print(f"监管态度评分: {analysis['regulatory_score']:.1f}/10")
        print(f"涉及领域: {', '.join(analysis['identified_domains'])}")
        print(f"强制程度: {analysis['enforcement_level']}")
    
    # 测试风险预警
    print("\n=== 风险预警测试 ===")
    alerts = trend_analyzer.generate_risk_alerts(sample_policies, threshold=7.0)
    print(f"生成 {len(alerts)} 个风险预警")
    for alert in alerts:
        print(f"⚠️  {alert['title'][:30]}... (评分: {alert['regulatory_score']:.1f})")

if __name__ == "__main__":
    main()