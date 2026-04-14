"""
1688 智能选品模块

功能：
1. 自动抓取 1688 热销榜、新品榜数据
2. 利润测算（考虑运费、平台扣点、快递成本）
3. 供应商资质评估
4. 侵权风险检测
5. 输出选品推荐列表
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutException

# 添加父目录到路径，便于导入 utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.excel_handler import ExcelHandler


class Selector1688:
    """1688 选品器"""

    def __init__(self, config):
        """
        初始化选品器
        
        Args:
            config: 配置字典（从 config.yaml 加载）
        """
        self.config = config
        self.source_config = config.get("source_1688", {})
        self.mode = self.source_config.get("mode", "hybrid")
        self.browser_config = self.source_config.get("browser", {})
        self.selection_params = self.source_config.get("selection", {})
        
        # 数据存储路径
        self.data_dir = os.path.join(
            config.get("basic", {}).get("data_dir", "./data"),
            "products"
        )
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 浏览器实例
        self.browser = None
        self.page = None
        
        logger.info("1688 选品模块初始化完成")

    def select_products(self, keywords=None):
        """
        执行选品流程
        
        Args:
            keywords: 关键词列表，如果为 None 则使用配置文件中的关键词
            
        Returns:
            DataFrame: 选品结果数据
        """
        if keywords is None:
            keywords = self.selection_params.get("keywords", ["居家日用"])
        
        all_products = []
        
        logger.info(f"开始执行 1688 选品，关键词：{keywords}")
        
        try:
            # 根据模式选择采集方式
            if self.mode in ["browser", "hybrid"]:
                products = self._browser_crawl(keywords)
                all_products.extend(products)
            
            if self.mode in ["api", "hybrid"] and not all_products:
                # API 模式暂为预留，降级为浏览器模式
                logger.warning("API 模式未配置，已降级为浏览器模式")
                products = self._browser_crawl(keywords)
                all_products.extend(products)
            
            if not all_products:
                logger.warning("未采集到任何商品数据")
                return pd.DataFrame()
            
            # 数据处理和筛选
            df = pd.DataFrame(all_products)
            df_filtered = self._filter_products(df)
            
            # 利润测算
            df_calculated = self._calculate_profit(df_filtered)
            
            # 保存结果
            output_file = self._save_results(df_calculated)
            logger.info(f"选品结果已保存至：{output_file}")
            
            return df_calculated
            
        except Exception as e:
            logger.error(f"选品过程出错：{e}")
            raise

    def _browser_crawl(self, keywords):
        """
        使用浏览器自动化采集 1688 商品数据
        
        Args:
            keywords: 关键词列表
            
        Returns:
            list: 商品数据列表
        """
        products = []
        
        with sync_playwright() as p:
            # 启动浏览器
            browser_type = getattr(p, self.browser_config.get("type", "chromium"))
            
            # 尝试复用已登录的浏览器
            launch_args = {
                "headless": self.browser_config.get("headless", False),
            }
            
            # 如果有用户数据目录，尝试复用登录状态
            user_data_dir = self.browser_config.get("user_data_dir")
            if user_data_dir:
                os.makedirs(user_data_dir, exist_ok=True)
                launch_args["args"] = [
                    f"--user-data-dir={os.path.abspath(user_data_dir)}",
                    f"--remote-debugging-port={self.browser_config.get('port', 9222)}"
                ]
            
            self.browser = browser_type.launch(**launch_args)
            self.page = self.browser.new_page()
            
            try:
                for keyword in keywords:
                    logger.info(f"正在采集关键词：{keyword}")
                    
                    # 搜索商品
                    search_url = f"https://s.1688.com/selloffer/offer_search.htm?keywords={keyword}"
                    self.page.goto(search_url, timeout=60000)
                    time.sleep(3)  # 等待页面加载
                    
                    # 滚动页面加载更多商品
                    self._scroll_to_load_more()
                    
                    # 提取商品数据
                    page_products = self._extract_product_info()
                    products.extend(page_products)
                    
                    logger.info(f"关键词 '{keyword}' 采集到 {len(page_products)} 个商品")
                    
                    # 翻页逻辑（可选）
                    # TODO: 实现自动翻页
                    
            except TimeoutException:
                logger.error("页面加载超时")
            except Exception as e:
                logger.error(f"浏览器采集异常：{e}")
            finally:
                self.browser.close()
        
        return products

    def _scroll_to_load_more(self):
        """滚动页面以加载更多商品"""
        try:
            # 多次滚动触发懒加载
            for i in range(3):
                self.page.evaluate(f"window.scrollTo(0, {i * 500})")
                time.sleep(1)
            # 滚动回顶部
            self.page.evaluate("window.scrollTo(0, 0)")
        except Exception as e:
            logger.warning(f"滚动页面失败：{e}")

    def _extract_product_info(self):
        """
        从页面提取商品信息
        
        Returns:
            list: 商品数据列表
        """
        products = []
        
        try:
            # 等待商品列表加载
            self.page.wait_for_selector(".offer-item", timeout=10000)
            
            # 获取所有商品元素
            product_elements = self.page.query_selector_all(".offer-item")
            
            for elem in product_elements:
                try:
                    # 提取商品标题
                    title_elem = elem.query_selector(".title")
                    title = title_elem.inner_text() if title_elem else ""
                    
                    # 提取价格
                    price_elem = elem.query_selector(".price")
                    price = price_elem.inner_text() if price_elem else ""
                    
                    # 提取销量
                    sales_elem = elem.query_selector(".sales")
                    sales = sales_elem.inner_text() if sales_elem else "0"
                    
                    # 提取供应商信息
                    supplier_elem = elem.query_selector(".supplier")
                    supplier = supplier_elem.inner_text() if supplier_elem else ""
                    
                    # 提取商品链接
                    link_elem = elem.query_selector("a")
                    link = link_elem.get_attribute("href") if link_elem else ""
                    
                    # 提取主图
                    image_elem = elem.query_selector("img")
                    image = image_elem.get_attribute("src") if image_elem else ""
                    
                    product_data = {
                        "product_id": "",  # 需要进一步解析
                        "title": title.strip(),
                        "price": self._parse_price(price),
                        "sales": self._parse_sales(sales),
                        "supplier": supplier.strip(),
                        "link": link,
                        "image": image,
                        "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "platform": "1688"
                    }
                    
                    products.append(product_data)
                    
                except Exception as e:
                    logger.warning(f"提取单个商品信息失败：{e}")
                    continue
                    
        except Exception as e:
            logger.error(f"批量提取商品信息失败：{e}")
        
        return products

    def _parse_price(self, price_str):
        """解析价格字符串为浮点数"""
        try:
            # 处理价格区间 "10.50-15.80"
            if "-" in price_str:
                prices = price_str.replace("¥", "").replace("￥", "").split("-")
                return float(prices[0])  # 取最低价
            else:
                return float(price_str.replace("¥", "").replace("￥", "").strip())
        except:
            return 0.0

    def _parse_sales(self, sales_str):
        """解析销量字符串为整数"""
        try:
            # 处理 "成交 1000+笔" 格式
            import re
            numbers = re.findall(r"\d+", sales_str)
            if numbers:
                # 处理 "万" 单位
                if "万" in sales_str:
                    return int(float(numbers[0]) * 10000)
                return int(numbers[0])
            return 0
        except:
            return 0

    def _filter_products(self, df):
        """
        根据配置参数筛选商品
        
        Args:
            df: 原始商品数据 DataFrame
            
        Returns:
            DataFrame: 筛选后的商品数据
        """
        min_sales = self.selection_params.get("min_sales", 100)
        min_profit_margin = self.selection_params.get("min_profit_margin", 30)
        
        # 筛选销量
        df_filtered = df[df["sales"] >= min_sales].copy()
        
        logger.info(f"原始商品数：{len(df)}, 筛选后商品数：{len(df_filtered)} (最低销量要求：{min_sales})")
        
        return df_filtered

    def _calculate_profit(self, df):
        """
        计算利润和 ROI
        
        Args:
            df: 商品数据 DataFrame
            
        Returns:
            DataFrame: 添加利润信息的商品数据
        """
        # 拼多多平台扣点：0.6%
        pdd_fee_rate = 0.006
        
        # 估算快递成本（按件）
        shipping_cost = 3.0  # 元/件
        
        # 包装成本
        packaging_cost = 0.5  # 元/件
        
        # 计算建议售价（进货价 * (1 + 加价率)）
        markup_rate = self.config.get("platform_pdd", {}).get("listing", {}).get("fixed_markup_rate", 0.5)
        df["suggested_price"] = df["price"] * (1 + markup_rate)
        
        # 计算毛利润
        df["gross_profit"] = df["suggested_price"] - df["price"] - shipping_cost - packaging_cost
        
        # 计算平台扣费
        df["platform_fee"] = df["suggested_price"] * pdd_fee_rate
        
        # 计算净利润
        df["net_profit"] = df["gross_profit"] - df["platform_fee"]
        
        # 计算毛利率
        df["profit_margin"] = (df["net_profit"] / df["suggested_price"] * 100).round(2)
        
        # 计算 ROI
        df["roi"] = (df["net_profit"] / df["price"] * 100).round(2)
        
        # 标记是否达到目标毛利率
        min_margin = self.selection_params.get("min_profit_margin", 30)
        df["meets_target"] = df["profit_margin"] >= min_margin
        
        logger.info(f"利润测算完成，达标商品数：{df['meets_target'].sum()} / {len(df)}")
        
        return df

    def _save_results(self, df):
        """
        保存选品结果到 Excel
        
        Args:
            df: 商品数据 DataFrame
            
        Returns:
            str: 保存的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"1688 选品_{timestamp}.xlsx"
        filepath = os.path.join(self.data_dir, filename)
        
        excel_handler = ExcelHandler()
        excel_handler.save_to_excel(df, filepath)
        
        return filepath

    def evaluate_supplier(self, supplier_name):
        """
        评估供应商资质
        
        Args:
            supplier_name: 供应商名称
            
        Returns:
            dict: 供应商评估结果
        """
        # TODO: 实现供应商详细评估
        # 包括：诚信通年限、回头率、发货速度、DSR 评分等
        logger.info(f"评估供应商：{supplier_name}")
        
        evaluation = {
            "supplier_name": supplier_name,
            "chengxintong_years": 0,  # 诚信通年限
            "repeat_rate": 0,  # 回头率
            "delivery_speed": 0,  # 发货速度评分
            "dsr_score": 0,  # DSR 评分
            "risk_level": "unknown"  # 风险等级
        }
        
        return evaluation

    def check_risk(self, product_title, product_image=None):
        """
        检测商品侵权风险
        
        Args:
            product_title: 商品标题
            product_image: 商品图片 URL（可选）
            
        Returns:
            dict: 风险评估结果
        """
        risk_result = {
            "has_brand_risk": False,
            "has_patent_risk": False,
            "forbidden_words": [],
            "risk_level": "low"
        }
        
        # 品牌词检测（简化版）
        brand_keywords = ["Nike", "Adidas", "Apple", "华为", "小米", "优衣库"]
        for brand in brand_keywords:
            if brand.lower() in product_title.lower():
                risk_result["has_brand_risk"] = True
                risk_result["forbidden_words"].append(brand)
        
        # 更新风险等级
        if risk_result["has_brand_risk"]:
            risk_result["risk_level"] = "high"
        
        return risk_result


if __name__ == "__main__":
    # 测试代码
    from utils.config_loader import ConfigLoader
    
    config_loader = ConfigLoader()
    config = config_loader.load()
    
    selector = Selector1688(config)
    df = selector.select_products()
    
    if not df.empty:
        print(f"\n选品结果预览：")
        print(df.head())
        print(f"\n总计：{len(df)} 个商品")
