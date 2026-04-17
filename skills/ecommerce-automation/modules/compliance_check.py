"""
风控合规检测模块

功能：
1. 违禁词检测
2. 广告法合规检查
3. 品牌侵权风险检测
4. 图片版权检测
5. 操作频率控制
"""

import os
import sys
import re
from datetime import datetime, timedelta
from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ComplianceCheck:
    """合规检测器"""

    def __init__(self, config):
        """
        初始化合规检测器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.compliance_config = config.get("compliance", {})
        
        # 加载违禁词库
        self.forbidden_words = self._load_forbidden_words()
        
        # 加载广告法敏感词
        self.advertising_law_words = self._load_advertising_law_words()
        
        # 加载品牌词库
        self.brand_words = self._load_brand_words()
        
        # 操作记录（用于频率控制）
        self.action_history = []
        
        logger.info("合规检测模块初始化完成")

    def check_title(self, title):
        """
        检测商品标题合规性
        
        Args:
            title: 商品标题
            
        Returns:
            dict: 检测结果
        """
        result = {
            "is_compliant": True,
            "forbidden_words_found": [],
            "advertising_law_violations": [],
            "brand_risks": [],
            "suggestions": []
        }
        
        if not title:
            result["is_compliant"] = False
            result["suggestions"].append("标题不能为空")
            return result
        
        # 违禁词检测
        if self.compliance_config.get("forbidden_words_check", True):
            forbidden_found = self._check_forbidden_words(title)
            if forbidden_found:
                result["is_compliant"] = False
                result["forbidden_words_found"] = forbidden_found
                result["suggestions"].append(f"发现违禁词：{', '.join(forbidden_found)}")
        
        # 广告法检测
        if self.compliance_config.get("advertising_law_check", True):
            ad_violations = self._check_advertising_law(title)
            if ad_violations:
                result["is_compliant"] = False
                result["advertising_law_violations"] = ad_violations
                result["suggestions"].append(f"违反广告法用语：{', '.join(ad_violations)}")
        
        # 品牌侵权检测
        brand_risks = self._check_brand_risk(title)
        if brand_risks:
            result["brand_risks"] = brand_risks
            result["suggestions"].append(f"可能涉及品牌侵权：{', '.join(brand_risks)}")
        
        return result

    def check_description(self, description):
        """
        检测商品详情页描述合规性
        
        Args:
            description: 商品描述
            
        Returns:
            dict: 检测结果
        """
        result = {
            "is_compliant": True,
            "issues": [],
            "suggestions": []
        }
        
        if not description:
            result["is_compliant"] = False
            result["suggestions"].append("商品描述不能为空")
            return result
        
        # 违禁词检测
        forbidden_found = self._check_forbidden_words(description)
        if forbidden_found:
            result["is_compliant"] = False
            result["issues"].append(f"发现违禁词：{len(forbidden_found)}个")
            result["forbidden_words"] = forbidden_found[:10]  # 只显示前 10 个
        
        # 广告法检测
        ad_violations = self._check_advertising_law(description)
        if ad_violations:
            result["is_compliant"] = False
            result["issues"].append(f"广告法敏感词：{len(ad_violations)}个")
            result["ad_violations"] = ad_violations[:10]
        
        return result

    def _check_forbidden_words(self, text):
        """
        检测违禁词
        
        Args:
            text: 待检测文本
            
        Returns:
            list: 发现的违禁词列表
        """
        found_words = []
        
        for word in self.forbidden_words:
            if word.lower() in text.lower():
                found_words.append(word)
        
        return found_words

    def _check_advertising_law(self, text):
        """
        检测广告法违规用语
        
        Args:
            text: 待检测文本
            
        Returns:
            list: 发现的违规用语列表
        """
        found_words = []
        
        for word_pattern in self.advertising_law_words:
            # 支持正则匹配
            if isinstance(word_pattern, str):
                if word_pattern in text:
                    found_words.append(word_pattern)
            else:
                # 正则表达式
                matches = re.findall(word_pattern, text, re.IGNORECASE)
                found_words.extend(matches)
        
        return found_words

    def _check_brand_risk(self, text):
        """
        检测品牌侵权风险
        
        Args:
            text: 待检测文本
            
        Returns:
            list: 发现的品牌词列表
        """
        found_brands = []
        
        for brand in self.brand_words:
            if brand.lower() in text.lower():
                found_brands.append(brand)
        
        return found_brands

    def _load_forbidden_words(self):
        """加载违禁词库"""
        # 常见违禁词（简化版，实际应该从文件加载完整词库）
        forbidden_words = [
            "国家级", "世界级", "最高级", "最佳", "第一", "唯一", "顶级",
            "极致", "永久", "特效", "精准", "万能", "祖传", "贵族",
            "特供", "专供", "点击领奖", "恭喜获奖", "全民免单", "秒杀",
            "抢爆", "再不抢就没了", "错过就没机会了", "无耻", "欺诈",
            "宗教相关", "政治敏感", "色情", "赌博", "毒品"
        ]
        
        # 尝试从文件加载更完整的词库
        try:
            word_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data",
                "forbidden_words.txt"
            )
            if os.path.exists(word_file):
                with open(word_file, "r", encoding="utf-8") as f:
                    file_words = [line.strip() for line in f if line.strip()]
                    forbidden_words.extend(file_words)
                logger.info(f"从文件加载了 {len(file_words)} 个违禁词")
        except Exception as e:
            logger.warning(f"加载违禁词文件失败：{e}")
        
        return forbidden_words

    def _load_advertising_law_words(self):
        """加载广告法敏感词"""
        advertising_words = [
            "最", "第一", "唯一", "顶级", "独家", "首创", "领先",
            r"国[家字]\s*级", r"全\s*国", r"全\s*球", "世界", "极品",
            "绝对", "100%", "零风险", "无副作用", "根治", "痊愈",
            "史无前例", "前无古人", "永久有效", "彻底解决"
        ]
        
        return advertising_words

    def _load_brand_words(self):
        """加载品牌词库"""
        brands = [
            "Nike", "Adidas", "Apple", "华为", "小米", "优衣库", "ZARA",
            "H&M", "香奈儿", "迪奥", "LV", "Gucci", "Prada", "Omega",
            "劳力士", "卡地亚", "特斯拉", "宝马", "奔驰", "奥迪"
        ]
        
        # 尝试从文件加载
        try:
            brand_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data",
                "brands.txt"
            )
            if os.path.exists(brand_file):
                with open(brand_file, "r", encoding="utf-8") as f:
                    file_brands = [line.strip() for line in f if line.strip()]
                    brands.extend(file_brands)
        except Exception as e:
            logger.warning(f"加载品牌词文件失败：{e}")
        
        return brands

    def can_perform_action(self, action_type):
        """
        检查是否可以执行某类操作（频率控制）
        
        Args:
            action_type: 操作类型 (listing / order / sync 等)
            
        Returns:
            bool: 是否允许执行
        """
        max_daily_listings = self.config.get("compliance", {}).get("max_daily_listings", 100)
        
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 清理历史记录（只保留今天的）
        self.action_history = [
            record for record in self.action_history
            if record["time"] > today_start
        ]
        
        # 统计今日同类操作次数
        today_count = sum(
            1 for record in self.action_history
            if record["type"] == action_type
        )
        
        if action_type == "listing" and today_count >= max_daily_listings:
            logger.warning(f"今日上架数量已达上限：{today_count}/{max_daily_listings}")
            return False
        
        # 检查操作间隔
        action_delay = self.config.get("compliance", {}).get("action_delay", 3)
        if self.action_history:
            last_action = max(
                (r for r in self.action_history if r["type"] == action_type),
                key=lambda x: x["time"],
                default=None
            )
            if last_action:
                time_diff = (now - last_action["time"]).total_seconds()
                if time_diff < action_delay:
                    logger.debug(f"操作间隔过短，等待 {action_delay - time_diff:.1f}秒")
                    return False
        
        # 记录本次操作
        self.action_history.append({
            "type": action_type,
            "time": now
        })
        
        return True

    def get_action_stats(self):
        """
        获取今日操作统计
        
        Returns:
            dict: 操作统计
        """
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 筛选今天的记录
        today_records = [r for r in self.action_history if r["time"] > today_start]
        
        # 按类型统计
        stats = {}
        for record in today_records:
            action_type = record["type"]
            stats[action_type] = stats.get(action_type, 0) + 1
        
        return stats

    def generate_compliance_report(self, products_df):
        """
        生成商品合规性报告
        
        Args:
            products_df: 商品数据 DataFrame
            
        Returns:
            DataFrame: 合规检测报告
        """
        logger.info(f"开始生成 {len(products_df)} 个商品的合规报告...")
        
        results = []
        
        for index, row in products_df.iterrows():
            title = row.get("title", "")
            
            # 检测标题
            title_result = self.check_title(title)
            
            result = {
                "product_id": row.get("product_id", index),
                "title": title[:50],
                "is_compliant": title_result["is_compliant"],
                "forbidden_words_count": len(title_result.get("forbidden_words_found", [])),
                "ad_violations_count": len(title_result.get("advertising_law_violations", [])),
                "brand_risks_count": len(title_result.get("brand_risks", [])),
                "issues": "; ".join(title_result.get("suggestions", []))
            }
            
            results.append(result)
        
        import pandas as pd
        df_report = pd.DataFrame(results)
        
        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(
            self.config.get("basic", {}).get("data_dir", "./data"),
            f"合规报告_{timestamp}.xlsx"
        )
        
        from utils.excel_handler import ExcelHandler
        excel_handler = ExcelHandler()
        excel_handler.save_to_excel(df_report, filepath)
        
        # 统计
        total = len(df_report)
        compliant = df_report["is_compliant"].sum()
        non_compliant = total - compliant
        
        logger.info(f"合规报告已生成：{filepath}")
        logger.info(f"合规商品：{compliant}/{total}, 不合规商品：{non_compliant}")
        
        return df_report


if __name__ == "__main__":
    from utils.config_loader import ConfigLoader
    
    config_loader = ConfigLoader()
    config = config_loader.load()
    
    checker = ComplianceCheck(config)
    
    # 测试标题检测
    test_titles = [
        "全网最低价！国家级品质保证",
        "正品 Nike 运动鞋 包邮",
        "居家收纳盒 实用好用",
        "史上最强清洁神器 永久有效"
    ]
    
    print("\n=== 标题合规检测测试 ===\n")
    for title in test_titles:
        result = checker.check_title(title)
        status = "✓ 合规" if result["is_compliant"] else "✗ 不合规"
        print(f"{status}: {title[:30]}...")
        if result["suggestions"]:
            for suggestion in result["suggestions"]:
                print(f"  → {suggestion}")
        print()
