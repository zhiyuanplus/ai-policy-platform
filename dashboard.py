# -*- coding: utf-8 -*-
"""
ARPI Platform - Interactive Dashboard
Powered by Streamlit and Plotly.
This version includes internationalization (i18n) for English and Chinese.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json

# --- I18N Text Configuration ---
TEXTS = {
    'en': {
        'page_title': "AI Regulatory & Policy (AIRP) Platform",
        'main_title': "AI Regulatory & Policy (AIRP) Platform",
        'lang_select': "Language",
        'error_no_data': "Analyzed data (all_policies_analyzed.csv) not found. Please run `python3 main.py` first to generate data.",
        'header_overview': "Overview",
        'metric_total': "Total Policies",
        'metric_avg_score': "Avg. Regulatory Score",
        'metric_date_range': "Date Range",
        'header_trend': "Regulatory Sentiment Trend",
        'caption_trend': "Score range 1-10. Higher score means stricter regulation. Score < 5 indicates a pro-innovation stance.",
        'radio_granularity': "Select time granularity:",
        'granularity_quarter': "Quarterly",
        'granularity_month': "Monthly",
        'granularity_year': "Yearly",
        'chart_trend_title': "Average Regulatory Score Trend",
        'chart_trend_xaxis': "Date",
        'chart_trend_yaxis': "Avg. Regulatory Score",
        'chart_neutral_line': "Neutral",
        'header_pie': "Policy Distribution by Department",
        'chart_pie_title': "Policy Distribution by Department",
        'pie_other_dept': "Other Departments",
        'header_bar': "Policy Legal Force Level",
        'chart_bar_title': "Distribution of Policy Legal Force",
        'chart_bar_xaxis': "Force Level",
        'chart_bar_yaxis': "Number of Documents",
        'header_details': "Policy Data Details",
        'expander_details': "Show/Hide Raw Data Columns",
        'header_reference': "Key AI Laws & Regulations Reference",
        'expander_reference': "Click to expand/collapse",
        'ref_intro': "Below are some of the core legal and policy documents in China's AI, algorithmic recommendation, and data security landscape.",
        'ref_cat_core': "Core Regulations & Measures",
        'ref_cat_foundational': "Foundational Laws",
        'ref_cat_strategy': "National Strategy & Planning",
        'ref_genai_title': "Interim Measures for the Management of Generative AI Services",
        'ref_genai_issuer': "Issued by: Cyberspace Administration of China (CAC) and six other departments",
        'ref_genai_date': "Effective Date: August 15, 2023",
        'ref_genai_desc': "Core Content: Regulates algorithm registration, training data, content labeling, and user protection for generative AI service providers.",
        'ref_deepsynth_title': "Provisions on the Management of Deep Synthesis Internet Information Services",
        'ref_deepsynth_issuer': "Issued by: CAC, Ministry of Industry and Information Technology (MIIT), Ministry of Public Security (MPS)",
        'ref_deepsynth_date': "Effective Date: January 10, 2023",
        'ref_deepsynth_desc': "Core Content: Requires deep synthesis service providers to add conspicuous labels and establish rumor refutation and review management systems.",
        'ref_algo_title': "Provisions on the Management of Algorithmic Recommendations in Internet Information Services",
        'ref_algo_issuer': "Issued by: CAC and three other departments",
        'ref_algo_date': "Effective Date: March 1, 2022",
        'ref_algo_desc': "Core Content: Regulates algorithm recommendation services, demanding protection of users' right to know and choose, and prohibiting discriminatory pricing ('big data price discrimination').",
        'ref_csl_title': "Cybersecurity Law of the People's Republic of China",
        'ref_csl_issuer': "Issued by: Standing Committee of the National People's Congress",
        'ref_csl_date': "Effective Date: June 1, 2017",
        'ref_csl_desc': "Core Content: China's foundational law in cybersecurity, establishing basic systems like the multi-level protection scheme (MLPS).",
        'ref_dsl_title': "Data Security Law of the People's Republic of China",
        'ref_dsl_issuer': "Issued by: Standing Committee of the National People's Congress",
        'ref_dsl_date': "Effective Date: September 1, 2021",
        'ref_dsl_desc': "Core Content: Establishes systems for classified and graded data management, data security risk assessment, monitoring, and emergency response.",
        'ref_pipl_title': "Personal Information Protection Law of the People's Republic of China",
        'ref_pipl_issuer': "Issued by: Standing Committee of the National People's Congress",
        'ref_pipl_date': "Effective Date: November 1, 2021",
        'ref_pipl_desc': "Core Content: Defines principles for personal information processing, with 'informed consent' as the core rule.",
        'ref_ngaip_title': "Next Generation Artificial Intelligence Development Plan",
        'ref_ngaip_issuer': "Issued by: The State Council",
        'ref_ngaip_date': "Release Date: July 8, 2017",
        'ref_ngaip_desc': "Core Content: The top-level design document for AI, establishing China's 'three-step' strategic goals for AI development."
    },
    'zh': {
        'page_title': "AI Regulatory & Policy (AIRP) Platform",
        'main_title': "AI Regulatory & Policy (AIRP) Platform",
        'lang_select': "语言",
        'error_no_data': "未找到分析数据 (all_policies_analyzed.csv). 请先运行 `python3 main.py` 生成数据。",
        'header_overview': "总体概览",
        'metric_total': "总政策数",
        'metric_avg_score': "平均监管评分",
        'metric_date_range': "数据时间范围",
        'header_trend': "监管情绪走势图",
        'caption_trend': "评分范围1-10，分数越高代表监管越严格，分数<5代表政策态度偏向鼓励创新。",
        'radio_granularity': "选择时间粒度:",
        'granularity_quarter': "季度",
        'granularity_month': "月度",
        'granularity_year': "年度",
        'chart_trend_title': "平均监管评分趋势",
        'chart_trend_xaxis': "时间",
        'chart_trend_yaxis': "平均监管评分",
        'chart_neutral_line': "中性线",
        'header_pie': "各部委发布权重",
        'chart_pie_title': "政策发布部门分布",
        'pie_other_dept': "其他部门",
        'header_bar': "政策法律效力层级",
        'chart_bar_title': "各项政策的法律效力分布",
        'chart_bar_xaxis': "效力层级",
        'chart_bar_yaxis': "文件数量",
        'header_details': "政策数据详情",
        'expander_details': "显示/隐藏 原始数据列",
        'header_reference': "主要人工智能法律法规参考",
        'expander_reference': "点击展开/折叠",
        'ref_intro': "以下是中国在人工智能、算法推荐和数据安全领域部分核心的法律、法规和国家政策文件。",
        'ref_cat_core': "核心法规与办法",
        'ref_cat_foundational': "基础性法律",
        'ref_cat_strategy': "国家战略与规划",
        'ref_genai_title': "《生成式人工智能服务管理暂行办法》",
        'ref_genai_issuer': "发布机构：国家互联网信息办公室等七部门",
        'ref_genai_date': "生效日期：2023年8月15日",
        'ref_genai_desc': "核心内容：对生成式AI服务提供者的算法备案、训练数据、内容标识、用户保护等方面作出规定。",
        'ref_deepsynth_title': "《互联网信息服务深度合成管理规定》",
        'ref_deepsynth_issuer': "发布机构：国家互联网信息办公室、工业和信息化部、公安部",
        'ref_deepsynth_date': "生效日期：2023年1月10日",
        'ref_deepsynth_desc': "核心内容：要求深度合成服务提供者进行显著标识，并建立健全辟谣机制和审核管理制度。",
        'ref_algo_title': "《互联网信息服务算法推荐管理规定》",
        'ref_algo_issuer': "发布机构：国家互联网信息办公室等四部门",
        'ref_algo_date': "生效日期：2022年3月1日",
        'ref_algo_desc': "核心内容：规范算法推荐服务，要求保障用户的知情权和选择权，禁止大数据杀熟等行为。",
        'ref_csl_title': "《中华人民共和国网络安全法》",
        'ref_csl_issuer': "发布机构：全国人民代表大会常务委员会",
        'ref_csl_date': "生效日期：2017年6月1日",
        'ref_csl_desc': "核心内容：中国网络安全领域的基础性法律，确立了网络安全等级保护等基本制度。",
        'ref_dsl_title': "《中华人民共和国数据安全法》",
        'ref_dsl_issuer': "发布机构：全国人民代表大会常务委员会",
        'ref_dsl_date': "生效日期：2021年9月1日",
        'ref_dsl_desc': "核心内容：确立了数据分类分级管理、数据安全风险评估、监测预警和应急处置等制度。",
        'ref_pipl_title': "《中华人民共和国个人信息保护法》",
        'ref_pipl_issuer': "发布机构：全国人民代表大会常务委员会",
        'ref_pipl_date': "生效日期：2021年11月1日",
        'ref_pipl_desc': "核心内容：明确了个人信息处理的各项原则，要求“告知-同意”为核心的个人信息处理规则。",
        'ref_ngaip_title': "《新一代人工智能发展规划》",
        'ref_ngaip_issuer': "发布机构：国务院",
        'ref_ngaip_date': "发布日期：2017年7月8日",
        'ref_ngaip_desc': "核心内容：确立了中国AI发展的“三步走”战略目标，是AI领域的顶层设计文件。"
    }
}

# --- Data Translation Mappings ---
DEPT_TRANSLATION = {
    '中华人民共和国工业和信息化部': 'MIIT',
    '国家互联网信息办公室': 'CAC',
    '全国信息安全标准化技术委员会': 'TC260',
    '国家市场监督管理总局': 'SAMR',
    '科技司': 'Science & Tech Dept.',
    '办公厅': 'General Office',
    '其他部门': 'Other Departments'
}

LEVEL_TRANSLATION = {
    '法律法规': 'Laws & Regulations',
    '行政规章': 'Administrative Rules',
    '行业标准': 'Industry Standards',
    '指导性文件': 'Guiding Documents'
}


# --- Page Configuration ---
st.set_page_config(
    page_title=TEXTS['en']['page_title'], # Default to EN
    layout="wide"
)

# --- Data Loading ---
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        return None, None
    df = pd.read_csv(file_path)
    df['publication_date'] = pd.to_datetime(df['publication_date'], errors='coerce')
    df.dropna(subset=['publication_date'], inplace=True)
    
    # Load metadata
    metadata_path = "metadata.json"
    overall_max_date = None
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            overall_max_date = pd.to_datetime(metadata.get('overall_max_date'))

    return df, overall_max_date

# --- Main Application ---
def main():
    # --- Language Selection ---
    _, col_lang, _ = st.columns([8, 2, 1])
    with col_lang:
        selected_language_label = st.radio(
            "Language / 语言",
            ('English', '中文'),
            index=1, # Default to Chinese
            horizontal=True,
            label_visibility="collapsed"
        )
    lang_code = 'en' if selected_language_label == 'English' else 'zh'
    T = TEXTS[lang_code]
    
    st.title(T['main_title'])

    df, overall_max_date = load_data("all_policies_analyzed.csv")

    if df is None:
        st.error(f"{T['error_no_data']}")
        return
        
    # Use overall_max_date for the range, but fallback to df's max date if not available
    xaxis_max = overall_max_date if overall_max_date is not None else df['publication_date'].max()

    st.header(T['header_overview'])
    total_policies, avg_score, min_date, max_date = len(df), df['regulatory_score'].mean(), df['publication_date'].min().strftime('%Y-%m-%d'), df['publication_date'].max().strftime('%Y-%m-%d')
    
    st.markdown(f"""
    <style>
        .metric-container {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; }}
        .metric {{ background-color: #f0f2f6; padding: 0.5rem 1rem; border-radius: 0.25rem; }}
        .metric-label {{ font-size: 0.9rem; color: #4f4f4f; }}
        .metric-value {{ font-size: 1.5rem; font-weight: 600; color: #262730; }}
    </style>
    <div class="metric-container">
        <div class="metric"><div class="metric-label">{T['metric_total']}</div><div class="metric-value">{total_policies}</div></div>
        <div class="metric"><div class="metric-label">{T['metric_avg_score']}</div><div class="metric-value">{avg_score:.2f}</div></div>
        <div class="metric"><div class="metric-label">{T['metric_date_range']}</div><div class="metric-value">{min_date} to {max_date}</div></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    st.header(T['header_trend'])
    st.caption(T['caption_trend'])
    
    granularity_options = (T['granularity_year'], T['granularity_quarter'], T['granularity_month'])
    time_granularity = st.radio(
        T['radio_granularity'],
        granularity_options,
        index=0,
        horizontal=True,
    )
    
    freq_map = {granularity_options[0]: 'Y', granularity_options[1]: 'Q', granularity_options[2]: 'M'}
    selected_freq = freq_map[time_granularity]

    monthly_trend = df.set_index('publication_date').resample(selected_freq).agg({
        'regulatory_score': 'mean',
        'title': 'count'
    }).rename(columns={'title': 'policy_count'}).reset_index()

    fig_trend = px.line(
        monthly_trend, x='publication_date', y='regulatory_score',
        title=f'{time_granularity} {T["chart_trend_title"]}',
        labels={'publication_date': T['chart_trend_xaxis'], 'regulatory_score': T['chart_trend_yaxis']},
        markers=True
    )
    fig_trend.update_layout(
        title_font_size=20,
        xaxis_range=[df['publication_date'].min(), xaxis_max]
    )
    fig_trend.add_hline(y=5.0, line_dash="dot", line_color="gray", annotation_text=T['chart_neutral_line'])
    st.plotly_chart(fig_trend, use_container_width=True)
    
    st.markdown("---")

    col_pie, col_bar = st.columns(2)

    with col_pie:
        st.header(T['header_pie'])
        if 'unified_department' in df.columns:
            dept_counts = df['unified_department'].value_counts().reset_index()
        else:
            dept_counts = df['issuing_department'].value_counts().reset_index()
            
        dept_counts.columns = ['department', 'count']
        
        threshold = max(dept_counts['count'].sum() * 0.05, 5)
        
        if len(dept_counts) > 5:
            other_count = dept_counts[dept_counts['count'] < threshold]['count'].sum()
            main_depts = dept_counts[dept_counts['count'] >= threshold]
            if other_count > 0:
                other_row = pd.DataFrame([{'department': T['pie_other_dept'], 'count': other_count}])
                dept_display = pd.concat([main_depts, other_row], ignore_index=True)
            else:
                dept_display = main_depts
        else:
            dept_display = dept_counts
        
        # Translate data for the chart if English is selected
        if lang_code == 'en':
            dept_display['department'] = dept_display['department'].map(DEPT_TRANSLATION).fillna(dept_display['department'])

        fig_pie = px.pie(dept_display, names='department', values='count', title=T['chart_pie_title'])
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        st.header(T['header_bar'])
        level_order = ['法律法规', '行政规章', '行业标准', '指导性文件']
        level_counts = df['enforcement_level'].value_counts().reindex(level_order).fillna(0).reset_index()
        level_counts.columns = ['level', 'count']

        # Translate data for the chart if English is selected
        if lang_code == 'en':
            level_counts['level'] = level_counts['level'].map(LEVEL_TRANSLATION).fillna(level_counts['level'])

        fig_bar = px.bar(
            level_counts, x='level', y='count',
            title=T['chart_bar_title'],
            labels={'level': T['chart_bar_xaxis'], 'count': T['chart_bar_yaxis']},
            color='level', text='count'
        )
        fig_bar.update_layout(xaxis_title=None, yaxis_title=T['chart_bar_yaxis'], showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
        
    st.markdown("---")
    
    st.header(T['header_details'])
    with st.expander(T['expander_details']):
        st.data_editor(
            df,
            column_config={
                "title": st.column_config.TextColumn(
                    "Title",
                    width="large"
                ),
            },
            disabled=True,
            hide_index=True,
        )

    st.markdown("---")

    st.header(T['header_reference'])
    with st.expander(T['expander_reference']):
        st.markdown(f"""
        {T['ref_intro']}
        
        #### {T['ref_cat_core']}
        - **<a href="http://www.cac.gov.cn/2023-07/13/c_1690898327029107.htm" target="_blank">{T['ref_genai_title']}</a>**
            - *{T['ref_genai_issuer']}*
            - *{T['ref_genai_date']}*
            - *{T['ref_genai_desc']}*

        - **<a href="http://www.cac.gov.cn/2022-12/11/c_1672221949514309.htm" target="_blank">{T['ref_deepsynth_title']}</a>**
            - *{T['ref_deepsynth_issuer']}*
            - *{T['ref_deepsynth_date']}*
            - *{T['ref_deepsynth_desc']}*

        - **<a href="http://www.cac.gov.cn/2022-01/04/c_1642894606364259.htm" target="_blank">{T['ref_algo_title']}</a>**
            - *{T['ref_algo_issuer']}*
            - *{T['ref_algo_date']}*
            - *{T['ref_algo_desc']}*

        #### {T['ref_cat_foundational']}
        - **<a href="http://www.npc.gov.cn/wxzl/gongbao/2017-02/28/content_2017265.htm" target="_blank">{T['ref_csl_title']}</a>**
            - *{T['ref_csl_issuer']}*
            - *{T['ref_csl_date']}*
            - *{T['ref_csl_desc']}*

        - **<a href="http://www.npc.gov.cn/npc/c30834/202106/7c978964a78c4548b642f9b36d33f345.shtml" target="_blank">{T['ref_dsl_title']}</a>**
            - *{T['ref_dsl_issuer']}*
            - *{T['ref_dsl_date']}*
            - *{T['ref_dsl_desc']}*

        - **<a href="http://www.npc.gov.cn/npc/c30834/202108/a8c4e3672c74491a80b53a172c0aa688.shtml" target="_blank">{T['ref_pipl_title']}</a>**
            - *{T['ref_pipl_issuer']}*
            - *{T['ref_pipl_date']}*
            - *{T['ref_pipl_desc']}*

        #### {T['ref_cat_strategy']}
        - **<a href="https://www.gov.cn/zhengce/content/2017-07/20/content_5211996.htm" target="_blank">{T['ref_ngaip_title']}</a>**
            - *{T['ref_ngaip_issuer']}*
            - *{T['ref_ngaip_date']}*
            - *{T['ref_ngaip_desc']}*
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()