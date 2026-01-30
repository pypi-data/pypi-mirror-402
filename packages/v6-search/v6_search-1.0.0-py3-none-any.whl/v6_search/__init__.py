import os
import re
import json
import requests
import jieba
import sys
import argparse
from typing import List, Dict, Optional, Any


class IntelligentSearch:
    """智能搜索类，提供基于Elasticsearch的多维度智能文档检索功能"""
    
    def __init__(self, es_url: str = None, es_index: str = None):
        """
        初始化智能搜索类
        
        Args:
            es_url: Elasticsearch URL，默认为环境变量ES_URL或"http://192.168.66.38:9200"
            es_index: Elasticsearch索引名，默认为环境变量ES_INDEX或"file_index"
        """
        self.es_url = es_url or os.getenv('ES_URL', "http://192.168.66.38:9200")
        self.es_index = es_index or os.getenv('ES_INDEX', "file_index")
        
    def estimate_tokens(self, text: str) -> int:
        """估算中文文本的Token数量（保守估计：1.5字符=1Token）"""
        if not text:
            return 0
        
        # 中文大致按1.5字符=1Token，英文按4字符=1Token
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)
    
    def smart_truncate(self, content: str, max_tokens: int) -> str:
        """在句子边界处智能截断内容"""
        if not content:
            return content
        
        estimated = self.estimate_tokens(content)
        if estimated <= max_tokens:
            return content
        
        # 计算最大字符数（保守估计）
        max_chars = int(max_tokens * 1.3)
        if len(content) <= max_chars:
            return content
        
        truncated = content[:max_chars]
        
        # 寻找合适的截断点（句子边界）
        boundaries = ['.', '。', '!', '！', '?', '？', '\n\n']
        for boundary in boundaries:
            last_index = truncated.rfind(boundary)
            if last_index > max_chars * 0.7:  # 确保截断点不太早
                return truncated[:last_index + 1] + f"\n\n(内容截断，原长度: {len(content)}字符)"
        
        # 如果没有找到合适边界，在段落边界截断
        last_paragraph = truncated.rfind('\n\n')
        if last_paragraph > max_chars * 0.5:
            return truncated[:last_paragraph] + f"\n\n(内容截断，原长度: {len(content)}字符)"
        
        return truncated + f"\n\n(内容截断，原长度: {len(content)}字符)"
    
    def extract_keywords(self, text: str) -> str:
        """使用jieba提取关键词"""
        words = jieba.cut_for_search(text)
        keywords = [word for word in words if len(word) > 1]  # 过滤掉单字符
        return ' '.join(keywords)
    
    def filename_relevance_score(self, query: str, filename: str) -> float:
        """基于文件名的相关性评分"""
        if not filename:
            return 0.0
        
        # 提取查询关键词
        query_keywords = set(self.extract_keywords(query).split())
        filename_keywords = set(self.extract_keywords(filename).split())
        
        if not query_keywords or not filename_keywords:
            return 0.0
        
        # 计算关键词匹配度（Jaccard相似度）
        intersection = len(query_keywords.intersection(filename_keywords))
        union = len(query_keywords.union(filename_keywords))
        
        if union == 0:
            return 0.0
        
        match_score = intersection / union
        
        # 时间相关性加分
        time_relevance = self.calculate_time_relevance(query, filename)
        
        # 文件类型加分
        file_type_bonus = self.calculate_file_type_bonus(query, filename)
        
        return match_score * 0.7 + time_relevance * 0.2 + file_type_bonus * 0.1
    
    def calculate_time_relevance(self, query: str, filename: str) -> float:
        """计算时间相关性"""
        # 提取文件名中的日期（格式：2023年12月、2023-12等）
        date_patterns = [
            r'(\d{4})年(\d{1,2})月',
            r'(\d{4})-(\d{1,2})',
            r'(\d{4})\.(\d{1,2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                # 如果查询中也包含时间信息，可以进一步计算时间接近度
                # 这里简单返回一个基础分数
                return 0.3
        
        return 0.0
    
    def calculate_file_type_bonus(self, query: str, filename: str) -> float:
        """计算文件类型加分"""
        table_keywords = ['表', '表格', '数据', '统计', '汇总', '报表', 'sheet', 'excel']
        query_has_table_terms = any(keyword in query for keyword in table_keywords)
        
        # 检查文件是否为表格格式
        is_table_file = any(filename.lower().endswith(ext) for ext in ['.xlsx', '.xls', '.csv'])
        
        if query_has_table_terms and is_table_file:
            return 0.5  # 表格查询+表格文件，高分匹配
        elif is_table_file:
            return 0.2  # 表格文件，中等加分
        else:
            return 0.0
    
    def optimize_search_query(self, query: str) -> Dict[str, Any]:
        """根据查询类型优化搜索参数"""
        table_keywords = ['表', '表格', '数据', '统计', '汇总', '报表']
        is_table_query = any(keyword in query for keyword in table_keywords)
        
        if is_table_query:
            # 表格查询：增大片段大小以包含更多数据行
            return {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["file_name^3", "content"],  # 文件名权重更高
                        "analyzer": "ik_max_word"
                    }
                },
                "highlight": {
                    "fields": {
                        "content": {
                            "fragment_size": 600,  # 增大片段大小
                            "number_of_fragments": 5,  # 增加片段数量
                            "pre_tags": [""],
                            "post_tags": [""],
                            "order": "score"
                        }
                    }
                },
                "size": 8,  # 获取更多文档进行选择
                "sort": [{"_score": {"order": "desc"}}],
                "_source": ["file_name", "file_path"]
            }
        else:
            # 普通文本查询
            return {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["file_name^2", "content"],  # 文件名权重适中
                        "analyzer": "ik_max_word"
                    }
                },
                "highlight": {
                    "fields": {
                        "content": {
                            "fragment_size": 300,
                            "number_of_fragments": 3,
                            "pre_tags": [""],
                            "post_tags": [""],
                            "order": "score"
                        }
                    }
                },
                "size": 5,
                "sort": [{"_score": {"order": "desc"}}],
                "_source": ["file_name", "file_path"]
            }
    
    def format_document_content(self, doc: Dict[str, Any], query: str) -> str:
        """格式化文档内容"""
        file_name = doc['file_name']
        content_snippets = doc['content_snippets']
        
        content = f"文件: {file_name}\n"
        
        if content_snippets:
            content += "相关片段:\n" + "\n".join(content_snippets)
        else:
            content += "（无高亮片段）"
        
        return content
    
    def load_content_by_priority(self, scored_documents: List[Dict[str, Any]], 
                                query: str, max_tokens: int) -> str:
        """按评分优先级加载内容"""
        relevant_content = ""
        current_tokens = 0
        
        for doc in scored_documents:
            if current_tokens >= max_tokens:
                break
                
            file_content = self.format_document_content(doc, query)
            content_tokens = self.estimate_tokens(file_content)
            
            if current_tokens + content_tokens <= max_tokens:
                relevant_content += file_content + "\n\n"
                current_tokens += content_tokens
            else:
                # 如果空间不足，尝试截断或摘要
                remaining_tokens = max_tokens - current_tokens
                if remaining_tokens > 100:  # 确保有足够空间
                    truncated_content = self.smart_truncate(file_content, remaining_tokens)
                    relevant_content += truncated_content + "\n\n"
                break
        
        return relevant_content
    
    def detect_specific_filename(self, query: str) -> Optional[str]:
        """检测用户问题是否指向具体文件名"""
        # 1. 精确文件名匹配模式
        filename_patterns = [
            r'附件\d+：.*?\.(xlsx|xls|doc|docx|pdf|txt)',  # 附件格式
            r'[《》].*?\.(xlsx|xls|doc|docx|pdf|txt)[》]',  # 书名号包含的文件名
            r'.*?表.*?\.(xlsx|xls)',  # 包含"表"字的Excel文件
            r'.*?报告.*?\.(doc|docx|pdf)',  # 包含"报告"字的文档
        ]
        
        for pattern in filename_patterns:
            match = re.search(pattern, query)
            if match:
                filename = match.group()
                # 清理文件名（去除书名号等）
                filename = filename.replace('《', '').replace('》', '')
                return filename
        
        # 2. 基于关键词的文件名推断
        if self.contains_filename_keywords(query):
            inferred_filename = self.infer_filename_from_query(query)
            if inferred_filename:
                return inferred_filename
        
        return None
    
    def contains_filename_keywords(self, query: str) -> bool:
        """检测查询中是否包含文件名关键词"""
        filename_indicators = [
            '附件', '表', '报告', '文件', '文档', '汇总表', '花名册',
            'xlsx', 'xls', 'doc', 'docx', 'pdf', 'txt'
        ]
        return any(indicator in query for indicator in filename_indicators)
    
    def infer_filename_from_query(self, query: str) -> Optional[str]:
        """从查询中推断可能的文件名模式"""
        # 基于时间推断
        year_month_match = re.search(r'(\d{4})年(\d{1,2})月', query)
        if year_month_match:
            year = year_month_match.group(1)
            month = year_month_match.group(2)
            return f"*{year}年{month}月*"
        
        # 基于主题推断
        if '特困' in query and '救助' in query:
            if '汇总' in query:
                return "*特困*救助汇总表*"
            elif '花名册' in query or '名单' in query:
                return "*特困*救助花名册*"
            else:
                return "*特困*救助*"
        
        if '低保' in query:
            if '农低保' in query:
                return "*农低保*"
            elif '城低保' in query:
                return "*城低保*"
            else:
                return "*低保*"
        
        return None
    
    def filename_directed_search(self, query: str, max_tokens: int = 8000) -> Optional[str]:
        """当检测到具体文件名时，优先加载完整内容"""
        filename_pattern = self.detect_specific_filename(query)
        if not filename_pattern:
            return None
        
        print(f"检测到文件名模式: {filename_pattern}")
        
        try:
            # 使用通配符搜索匹配的文件名
            es_query = {
                "query": {
                    "wildcard": {
                        "file_name": {
                            "value": filename_pattern
                        }
                    }
                },
                "size": 3,  # 返回最多3个匹配文件
                "sort": [{"_score": {"order": "desc"}}],
                "_source": ["file_name", "content", "file_path"]
            }
            
            response = requests.post(
                f"{self.es_url}/{self.es_index}/_search",
                json=es_query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            hits = data.get('hits', {}).get('hits', [])
            
            if not hits:
                print("未找到匹配的文件")
                return None
            
            # 处理匹配的文件
            relevant_content = ""
            current_tokens = 0
            
            for hit in hits:
                if current_tokens >= max_tokens:
                    break
                    
                file_name = hit['_source'].get('file_name', '')
                full_content = hit['_source'].get('content', '')
                
                if not full_content:
                    continue
                
                file_content = self.process_full_file_content(file_name, full_content, max_tokens - current_tokens)
                content_tokens = self.estimate_tokens(file_content)
                
                if current_tokens + content_tokens <= max_tokens:
                    relevant_content += file_content + "\n\n"
                    current_tokens += content_tokens
                else:
                    # 空间不足时进行截断
                    remaining_tokens = max_tokens - current_tokens
                    if remaining_tokens > 100:
                        truncated_content = self.smart_truncate(file_content, remaining_tokens)
                        relevant_content += truncated_content + "\n\n"
                    break
            
            if relevant_content:
                print(f"文件名导向搜索完成，返回Token数: {self.estimate_tokens(relevant_content)}")
                return relevant_content
            else:
                return None
                
        except Exception as e:
            print(f"文件名导向搜索错误: {e}")
            return None
    
    def process_full_file_content(self, file_name: str, full_content: str, max_tokens: int) -> str:
        """处理完整文件内容的智能策略"""
        content_tokens = self.estimate_tokens(full_content)
        
        if content_tokens <= max_tokens:
            # 如果内容在Token限制内，返回完整内容
            return f"文件: {file_name}\n完整内容:\n{full_content}"
        else:
            # 如果内容过长，采用分层加载策略
            return self.hierarchical_content_loading(file_name, full_content, max_tokens)
    
    def hierarchical_content_loading(self, file_name: str, full_content: str, max_tokens: int) -> str:
        """分层加载大文件内容"""
        # 1. 首先提取文件结构信息
        structure_content = self.extract_file_structure(full_content)
        structure_tokens = self.estimate_tokens(structure_content)
        
        remaining_tokens = max_tokens - structure_tokens
        
        if remaining_tokens > 500:  # 确保有足够空间加载部分数据
            # 2. 加载核心数据部分
            core_data = self.extract_core_data(full_content, remaining_tokens)
            return f"文件: {file_name}\n文件结构:\n{structure_content}\n核心数据:\n{core_data}"
        else:
            # 3. 空间有限，只返回文件结构
            return f"文件: {file_name}\n文件结构:\n{structure_content}\n(内容过长，已精简显示)"
    
    def extract_file_structure(self, content: str) -> str:
        """提取文件结构信息（适用于表格和文档）"""
        lines = content.split('\n')
        
        # 提取标题行和关键结构信息
        structure_lines = []
        for i, line in enumerate(lines[:100]):  # 检查前100行
            if self.is_structure_line(line):
                structure_lines.append(line)
            if len(structure_lines) >= 15:  # 最多15行结构信息
                break
        
        return '\n'.join(structure_lines) if structure_lines else "（无法提取结构信息）"
    
    def is_structure_line(self, line: str) -> bool:
        """判断是否为结构行（标题、表头等）"""
        line = line.strip()
        if len(line) < 3:
            return False
        
        structure_indicators = ['标题', '表头', '序号', '姓名', '金额', '日期', '单位', '附件', '表', '汇总']
        table_indicators = ['|', '---', '===', '工作表']
        
        return (any(indicator in line for indicator in structure_indicators) or
                any(indicator in line for indicator in table_indicators) or
                (len(line) > 20 and ' ' not in line and '\t' not in line))  # 长无空格行可能是表头
    
    def extract_core_data(self, content: str, max_tokens: int) -> str:
        """提取核心数据部分"""
        lines = content.split('\n')
        data_lines = []
        current_tokens = 0
        
        for line in lines:
            if current_tokens >= max_tokens:
                break
            
            line_tokens = self.estimate_tokens(line)
            if current_tokens + line_tokens <= max_tokens:
                # 优先选择包含数据的行
                if self.contains_data(line):
                    data_lines.append(line)
                    current_tokens += line_tokens
            else:
                break
        
        return '\n'.join(data_lines) if data_lines else "（无核心数据）"
    
    def contains_data(self, line: str) -> bool:
        """判断行是否包含数据"""
        line = line.strip()
        # 包含数字且长度适中的行可能包含数据
        return (any(char.isdigit() for char in line) and 
                5 < len(line) < 200 and
                not line.startswith('===') and
                not line.startswith('---'))
    
    def intelligent_es_search_with_scoring(self, query: str, max_tokens: int = 8000) -> str:
        """基于文件名评分的智能内容选择（集成文件名导向搜索）"""
        # 首先尝试文件名导向搜索
        filename_result = self.filename_directed_search(query, max_tokens)
        if filename_result:
            print("使用文件名导向搜索模式")
            return filename_result
        
        # 如果没有检测到具体文件名，使用原有的智能搜索
        print("使用普通智能搜索模式")
        return self.intelligent_general_search(query, max_tokens)
    
    def intelligent_general_search(self, query: str, max_tokens: int = 8000) -> str:
        """原有的智能搜索逻辑"""
        try:
            # 优化搜索参数，特别是对于表格文件
            es_query = self.optimize_search_query(query)
            
            response = requests.post(
                f"{self.es_url}/{self.es_index}/_search",
                json=es_query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            hits = data.get('hits', {}).get('hits', [])
            
            if not hits:
                print("未找到相关文档")
                return ""
            
            # 计算每个文档的综合评分
            scored_documents = []
            for hit in hits:
                file_name = hit['_source'].get('file_name', '')
                score = self.filename_relevance_score(query, file_name)
                
                # 获取高亮片段
                content_snippets = []
                if 'highlight' in hit and 'content' in hit['highlight']:
                    content_snippets = hit['highlight']['content']
                
                scored_documents.append({
                    'file_name': file_name,
                    'file_path': hit['_source'].get('file_path', ''),
                    'score': score,
                    'content_snippets': content_snippets,
                    'es_score': hit.get('_score', 0)
                })
            
            # 按综合评分排序（文件名相关性优先）
            scored_documents.sort(key=lambda x: x['score'], reverse=True)
            
            # 按优先级加载内容
            relevant_content = self.load_content_by_priority(scored_documents, query, max_tokens)
            
            print(f"智能搜索完成，返回Token数: {self.estimate_tokens(relevant_content)}")
            print(f"文档评分结果: {[(doc['file_name'], round(doc['score'], 2)) for doc in scored_documents[:3]]}")
            
            return relevant_content
            
        except Exception as e:
            print(f"智能搜索错误: {e}")
            return self.fallback_search(query)
    
    def fallback_search(self, query: str) -> str:
        """回退搜索方法，使用原始API"""
        try:
            search_url = os.getenv('SEARCH_URL')
            if not search_url:
                return ""
                
            payload = {
                "q": query,
                "type": "",
                "page": 1,
                "size": 5  # 减少返回数量
            }
            
            response = requests.post(search_url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('results'):
                # 提取内容预览并截断
                content_previews = []
                for result in data['results']:
                    if result.get('content_preview'):
                        content = result['content_preview']
                        # 对每个预览内容进行截断
                        truncated = self.smart_truncate(content, 1600)  # 每个文档约1600 tokens
                        content_previews.append(truncated)
                
                combined_content = '\n'.join(content_previews)
                # 整体截断
                return self.smart_truncate(combined_content, 8000)
            return ""
        except Exception as e:
            print(f"回退搜索错误: {e}")
            return ""
