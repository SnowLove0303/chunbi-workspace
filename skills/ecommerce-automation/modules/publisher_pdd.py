"""
拼多多商品上架模块

功能：
1. 商品标题优化（SEO）
2. 主图和详情页处理
3. 一键发布到拼多多商家后台
4. SKU 多规格定价
5. 库存自动设置
6. 多店铺管理
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutException

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.excel_handler import ExcelHandler


class PublisherPDD:
    """拼多多商品上架器"""

    def __init__(self, config):
        """
        初始化上架器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.platform_config = config.get("platform_pdd", {})
        self.mode = self.platform_config.get("mode", "hybrid")
        self.browser_config = self.platform_config.get("browser", {})
        self.listing_params = self.platform_config.get("listing", {})
        self.shops = self.platform_config.get("shops", [])
        
        # 当前激活的店铺
        self.current_shop = None
        for shop in self.shops:
            if shop.get("status") == "active":
                self.current_shop = shop
                break
        
        if not self.current_shop:
            logger.warning("未找到激活的店铺，请检查配置文件")
        
        # 浏览器实例
        self.browser = None
        self.page = None
        
        # 数据存储路径
        self.data_dir = os.path.join(
            config.get("basic", {}).get("data_dir", "./data"),
            "products"
        )
        
        logger.info("拼多多上架模块初始化完成")

    def publish_products(self, products_df=None, shop_id=None):
        """
        发布商品到拼多多
        
        Args:
            products_df: 商品数据 DataFrame（来自 1688 选品结果）
            shop_id: 店铺 ID，如果为 None 则使用当前激活店铺
            
        Returns:
            dict: 发布结果统计
        """
        if shop_id:
            # 切换店铺
            for shop in self.shops:
                if shop.get("shop_id") == shop_id:
                    self.current_shop = shop
                    break
        
        if not self.current_shop:
            logger.error("没有可用的店铺")
            return {"success": 0, "failed": 0, "error": "无可用店铺"}
        
        logger.info(f"开始发布商品到店铺：{self.current_shop['shop_name']}")
        
        # 加载商品数据
        if products_df is None:
            products_df = self._load_products_from_1688()
        
        if products_df is None or products_df.empty:
            logger.warning("没有可发布的商品")
            return {"success": 0, "failed": 0}
        
        # 限制单次发布数量
        batch_size = min(len(products_df), 50)
        products_df = products_df.head(batch_size)
        
        results = {
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        try:
            with sync_playwright() as p:
                # 启动浏览器
                browser_type = getattr(p, self.browser_config.get("type", "chromium"))
                
                launch_args = {
                    "headless": self.browser_config.get("headless", False),
                }
                
                # 复用已登录的浏览器
                user_data_dir = self.browser_config.get("user_data_dir")
                if user_data_dir:
                    os.makedirs(user_data_dir, exist_ok=True)
                    launch_args["args"] = [
                        f"--user-data-dir={os.path.abspath(user_data_dir)}",
                        f"--remote-debugging-port={self.browser_config.get('port', 9223)}"
                    ]
                
                self.browser = browser_type.launch(**launch_args)
                self.page = self.browser.new_page()
                
                # 登录拼多多商家后台
                if not self._login_pdd():
                    logger.error("登录失败")
                    return {"success": 0, "failed": len(products_df), "error": "登录失败"}
                
                # 逐个发布商品
                for index, row in products_df.iterrows():
                    logger.info(f"正在发布第 {index + 1}/{len(products_df)} 个商品：{row.get('title', '')[:30]}...")
                    
                    try:
                        success = self._publish_single_product(row)
                        
                        if success:
                            results["success"] += 1
                            results["details"].append({
                                "product_title": row.get("title", ""),
                                "status": "success"
                            })
                        else:
                            results["failed"] += 1
                            results["details"].append({
                                "product_title": row.get("title", ""),
                                "status": "failed"
                            })
                        
                        # 操作间隔控制（防风控）
                        action_delay = self.config.get("compliance", {}).get("action_delay", 3)
                        time.sleep(action_delay)
                        
                    except Exception as e:
                        logger.error(f"发布商品失败：{e}")
                        results["failed"] += 1
                        results["details"].append({
                            "product_title": row.get("title", ""),
                            "status": "error",
                            "error": str(e)
                        })
                
                logger.info(f"发布完成：成功 {results['success']} 个，失败 {results['failed']} 个")
                
        except Exception as e:
            logger.error(f"批量发布过程出错：{e}")
        finally:
            if self.browser:
                self.browser.close()
        
        # 保存发布结果
        self._save_publish_results(results)
        
        return results

    def _login_pdd(self):
        """
        登录拼多多商家后台
        
        Returns:
            bool: 是否登录成功
        """
        try:
            login_url = "https://mms.pinduoduo.com/login"
            self.page.goto(login_url, timeout=60000)
            
            # 等待页面加载
            time.sleep(3)
            
            # 检查是否已登录
            if "login" not in self.page.url.lower():
                logger.info("检测到已登录状态")
                return True
            
            # 提示用户手动扫码登录
            logger.info("请扫描二维码登录拼多多商家后台...")
            
            # 等待登录（最长等待 2 分钟）
            try:
                self.page.wait_for_url("https://mms.pinduoduo.com/*", timeout=120000)
                logger.info("登录成功")
                return True
            except TimeoutException:
                logger.error("登录超时")
                return False
                
        except Exception as e:
            logger.error(f"登录过程出错：{e}")
            return False

    def _publish_single_product(self, product_data):
        """
        发布单个商品
        
        Args:
            product_data: 商品数据（Series 对象）
            
        Returns:
            bool: 是否发布成功
        """
        try:
            # 进入商品发布页面
            publish_url = "https://mms.pinduoduo.com/product/publish"
            self.page.goto(publish_url, timeout=60000)
            time.sleep(3)
            
            # 优化标题
            optimized_title = self._optimize_title(product_data.get("title", ""))
            
            # 填写商品标题
            try:
                title_input = self.page.query_selector('input[name="goods_name"]')
                if title_input:
                    title_input.fill(optimized_title)
            except Exception as e:
                logger.warning(f"填写标题失败：{e}")
            
            # 填写商品价格
            price = product_data.get("suggested_price", 0)
            if price > 0:
                try:
                    price_input = self.page.query_selector('input[name="price"]')
                    if price_input:
                        price_input.fill(str(price))
                except Exception as e:
                    logger.warning(f"填写价格失败：{e}")
            
            # 填写库存
            stock = 999  # 默认库存
            try:
                stock_input = self.page.query_selector('input[name="stock"]')
                if stock_input:
                    stock_input.fill(str(stock))
            except Exception as e:
                logger.warning(f"填写库存失败：{e}")
            
            # TODO: 上传图片、填写详情、选择类目的逻辑需要进一步完善
            
            # 提交发布（需要人工确认，这里只做填充）
            logger.info(f"商品信息已填充，请人工确认后提交：{optimized_title}")
            
            return True
            
        except Exception as e:
            logger.error(f"发布单个商品失败：{e}")
            return False

    def _optimize_title(self, original_title):
        """
        优化商品标题（SEO）
        
        Args:
            original_title: 原始标题
            
        Returns:
            str: 优化后的标题
        """
        prefix = self.listing_params.get("title_prefix", "")
        suffix = self.listing_params.get("title_suffix", "包邮 正品 热销")
        
        # 拼多多标题建议长度：30-60 字符
        max_length = 60
        
        # 构建新标题
        parts = []
        if prefix:
            parts.append(prefix)
        parts.append(original_title.strip())
        if suffix:
            parts.append(suffix)
        
        new_title = " ".join(parts)
        
        # 截断过长的标题
        if len(new_title) > max_length:
            new_title = new_title[:max_length - 3] + "..."
        
        logger.debug(f"原标题：{original_title[:20]}... -> 优化后：{new_title[:30]}...")
        
        return new_title

    def _load_products_from_1688(self):
        """
        从 1688 选品结果中加载待发布商品
        
        Returns:
            DataFrame: 商品数据
        """
        try:
            # 查找最新的选品文件
            files = os.listdir(self.data_dir)
            xlsx_files = [f for f in files if f.startswith("1688 选品") and f.endswith(".xlsx")]
            
            if not xlsx_files:
                logger.warning("未找到 1688 选品文件")
                return None
            
            # 按时间排序，取最新的一个
            latest_file = sorted(xlsx_files)[-1]
            filepath = os.path.join(self.data_dir, latest_file)
            
            logger.info(f"加载选品文件：{latest_file}")
            
            df = pd.read_excel(filepath)
            
            # 筛选达标的商品
            if "meets_target" in df.columns:
                df = df[df["meets_target"] == True]
            
            return df
            
        except Exception as e:
            logger.error(f"加载选品文件失败：{e}")
            return None

    def _save_publish_results(self, results):
        """
        保存发布结果
        
        Args:
            results: 发布结果字典
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"发布结果_{timestamp}.xlsx"
        filepath = os.path.join(self.data_dir, filename)
        
        df_results = pd.DataFrame(results.get("details", []))
        
        excel_handler = ExcelHandler()
        excel_handler.save_to_excel(df_results, filepath)
        
        logger.info(f"发布结果已保存：{filepath}")

    def switch_shop(self, shop_id):
        """
        切换当前店铺
        
        Args:
            shop_id: 店铺 ID
        """
        for shop in self.shops:
            if shop.get("shop_id") == shop_id:
                # 先停用当前店铺
                if self.current_shop:
                    self.current_shop["status"] = "inactive"
                
                # 激活新店铺
                shop["status"] = "active"
                self.current_shop = shop
                
                logger.info(f"已切换到店铺：{shop['shop_name']}")
                return True
        
        logger.error(f"未找到店铺：{shop_id}")
        return False

    def list_shops(self):
        """
        列出所有店铺
        
        Returns:
            list: 店铺列表
        """
        return self.shops

    def set_pricing_strategy(self, strategy, markup_rate=None):
        """
        设置定价策略
        
        Args:
            strategy: 策略类型 (fixed / dynamic)
            markup_rate: 加价比例（固定策略时使用）
        """
        self.listing_params["pricing_strategy"] = strategy
        if markup_rate is not None:
            self.listing_params["fixed_markup_rate"] = markup_rate
        
        logger.info(f"定价策略已更新：{strategy}, 加价率：{markup_rate}")


if __name__ == "__main__":
    # 测试代码
    from utils.config_loader import ConfigLoader
    
    config_loader = ConfigLoader()
    config = config_loader.load()
    
    publisher = PublisherPDD(config)
    
    # 列出店铺
    print("\n可用店铺：")
    for shop in publisher.list_shops():
        status = "✓" if shop.get("status") == "active" else "✗"
        print(f"  {status} {shop['shop_name']} ({shop['shop_id']})")
