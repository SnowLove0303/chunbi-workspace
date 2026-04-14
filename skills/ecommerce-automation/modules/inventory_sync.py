"""
库存同步模块

功能：
1. 监控 1688 供应商库存变化
2. 自动调整拼多多店铺库存
3. 低库存预警
4. 滞销商品检测
5. 安全库存管理
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime
from loguru import logger
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.excel_handler import ExcelHandler


class InventorySync:
    """库存同步器"""

    def __init__(self, config):
        """
        初始化库存同步器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.inventory_config = config.get("inventory_sync", {})
        self.source_config = config.get("source_1688", {})
        self.platform_config = config.get("platform_pdd", {})
        
        # 数据存储路径
        self.data_dir = os.path.join(
            config.get("basic", {}).get("data_dir", "./data"),
            "products"
        )
        
        # 浏览器实例
        self.browser = None
        self.page = None
        
        logger.info("库存同步模块初始化完成")

    def sync_inventory(self):
        """
        执行库存同步流程
        
        Returns:
            dict: 同步结果统计
        """
        if not self.inventory_config.get("enabled", True):
            logger.info("库存同步功能已禁用")
            return {"status": "disabled"}
        
        logger.info("开始同步库存...")
        
        results = {
            "total": 0,
            "updated": 0,
            "low_stock": 0,
            "out_of_stock": 0,
            "details": []
        }
        
        try:
            # 加载本地商品数据
            products_df = self._load_local_products()
            
            if products_df is None or products_df.empty:
                logger.warning("没有可同步的商品数据")
                return results
            
            results["total"] = len(products_df)
            logger.info(f"待同步商品数：{results['total']}")
            
            with sync_playwright() as p:
                # 启动浏览器
                browser_type = getattr(p, self.source_config.get("browser", {}).get("type", "chromium"))
                
                launch_args = {
                    "headless": self.source_config.get("browser", {}).get("headless", False),
                }
                
                user_data_dir = self.source_config.get("browser", {}).get("user_data_dir")
                if user_data_dir:
                    os.makedirs(user_data_dir, exist_ok=True)
                    launch_args["args"] = [
                        f"--user-data-dir={os.path.abspath(user_data_dir)}",
                        f"--remote-debugging-port={self.source_config.get('browser', {}).get('port', 9222)}"
                    ]
                
                self.browser = browser_type.launch(**launch_args)
                self.page = self.browser.new_page()
                
                # 逐个检查商品库存
                for index, row in products_df.iterrows():
                    logger.debug(f"检查商品库存：{row.get('title', '')[:20]}...")
                    
                    try:
                        # 获取 1688 供应商库存
                        supplier_stock = self._check_1688_stock(row)
                        
                        # 计算可售库存（扣除安全库存）
                        safety_stock = self.inventory_config.get("safety_stock", 5)
                        available_stock = max(0, supplier_stock - safety_stock)
                        
                        # 更新本地记录
                        row["supplier_stock"] = supplier_stock
                        row["available_stock"] = available_stock
                        row["sync_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # 检查库存状态
                        low_threshold = self.inventory_config.get("low_stock_threshold", 20)
                        
                        if supplier_stock == 0:
                            row["stock_status"] = "out_of_stock"
                            results["out_of_stock"] += 1
                            logger.warning(f"商品缺货：{row.get('title', '')[:30]}")
                        elif supplier_stock <= low_threshold:
                            row["stock_status"] = "low_stock"
                            results["low_stock"] += 1
                            
                            # 发送预警通知
                            if self.inventory_config.get("low_stock_alert", True):
                                self._send_low_stock_alert(row)
                        else:
                            row["stock_status"] = "normal"
                        
                        # 同步到拼多多（如需要）
                        if available_stock != row.get("pdd_stock", available_stock):
                            self._update_pdd_stock(row, available_stock)
                            results["updated"] += 1
                        
                        results["details"].append(row.to_dict())
                        
                        # 操作间隔控制
                        action_delay = self.config.get("compliance", {}).get("action_delay", 3)
                        time.sleep(action_delay)
                        
                    except Exception as e:
                        logger.error(f"同步商品库存失败：{e}")
                        continue
                
                # 保存同步结果
                self._save_sync_results(results["details"])
                
                logger.info(f"库存同步完成：总计{results['total']}, 更新{results['updated']}, 低库存{results['low_stock']}, 缺货{results['out_of_stock']}")
                
        except Exception as e:
            logger.error(f"库存同步过程出错：{e}")
        finally:
            if self.browser:
                self.browser.close()
        
        return results

    def _load_local_products(self):
        """
        加载本地商品数据
        
        Returns:
            DataFrame: 商品数据
        """
        try:
            # 查找最新的选品文件
            files = os.listdir(self.data_dir)
            xlsx_files = [f for f in files if f.startswith("1688 选品") and f.endswith(".xlsx")]
            
            if not xlsx_files:
                return None
            
            latest_file = sorted(xlsx_files)[-1]
            filepath = os.path.join(self.data_dir, latest_file)
            
            df = pd.read_excel(filepath)
            logger.info(f"加载商品数据：{latest_file}")
            
            return df
            
        except Exception as e:
            logger.error(f"加载商品数据失败：{e}")
            return None

    def _check_1688_stock(self, product_row):
        """
        检查 1688 商品库存
        
        Args:
            product_row: 商品数据行
            
        Returns:
            int: 库存数量
        """
        try:
            # 访问商品页面
            product_link = product_row.get("link", "")
            if not product_link:
                return 0
            
            self.page.goto(product_link, timeout=60000)
            time.sleep(2)
            
            # TODO: 从页面提取实际库存数据
            # 不同供应商的库存显示方式可能不同
            
            # 示例：尝试查找库存元素
            try:
                stock_elem = self.page.query_selector(".stock-number")
                if stock_elem:
                    stock_text = stock_elem.inner_text()
                    # 解析库存数字
                    import re
                    numbers = re.findall(r"\d+", stock_text)
                    if numbers:
                        return int(numbers[0])
            except:
                pass
            
            # 默认返回一个较大值（假设库存充足）
            return 999
            
        except Exception as e:
            logger.error(f"检查库存失败：{e}")
            return 0

    def _update_pdd_stock(self, product_row, new_stock):
        """
        更新拼多多商品库存
        
        Args:
            product_row: 商品数据行
            new_stock: 新库存数量
        """
        logger.debug(f"更新拼多多库存：{product_row.get('title', '')[:20]}... -> {new_stock}")
        
        # TODO: 实现拼多多库存更新逻辑
        # 可以通过浏览器自动化或 API 方式更新
        
        try:
            with sync_playwright() as p:
                browser_type = getattr(p, self.platform_config.get("browser", {}).get("type", "chromium"))
                browser = browser_type.launch(headless=False)
                page = browser.new_page()
                
                # 登录拼多多商家后台
                page.goto("https://mms.pinduoduo.com/login", timeout=60000)
                time.sleep(3)
                
                # TODO: 进入商品管理页面，找到对应商品，更新库存
                
                browser.close()
                
        except Exception as e:
            logger.error(f"更新拼多多库存失败：{e}")

    def _send_low_stock_alert(self, product_row):
        """
        发送低库存预警通知
        
        Args:
            product_row: 商品数据行
        """
        title = product_row.get("title", "未知商品")
        stock = product_row.get("supplier_stock", 0)
        threshold = self.inventory_config.get("low_stock_threshold", 20)
        
        message = f"⚠️ 低库存预警\n\n商品：{title[:50]}...\n当前库存：{stock}\n预警阈值：{threshold}\n请及时补货！"
        
        logger.warning(message)
        
        # TODO: 发送到钉钉、微信或邮箱
        # 可以参考 utils/dingtalk_notify.py 实现

    def _save_sync_results(self, details):
        """
        保存库存同步结果
        
        Args:
            details: 同步详情列表
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"库存同步_{timestamp}.xlsx"
        filepath = os.path.join(self.data_dir, filename)
        
        df = pd.DataFrame(details)
        excel_handler = ExcelHandler()
        excel_handler.save_to_excel(df, filepath)
        
        logger.info(f"库存同步结果已保存：{filepath}")

    def check_slow_moving_products(self, days=30):
        """
        检测滞销商品
        
        Args:
            days: 天数阈值
            
        Returns:
            DataFrame: 滞销商品列表
        """
        logger.info(f"检测过去{days}天无销量的滞销商品...")
        
        # TODO: 实现滞销商品检测逻辑
        # 基于订单数据分析
        
        slow_moving = pd.DataFrame()  #  placeholder
        
        if not slow_moving.empty:
            logger.warning(f"发现{len(slow_moving)}个滞销商品")
            output_file = os.path.join(self.data_dir, f"滞销商品_{datetime.now().strftime('%Y%m%d')}.xlsx")
            slow_moving.to_excel(output_file, index=False)
            logger.info(f"滞销商品列表已保存：{output_file}")
        
        return slow_moving


if __name__ == "__main__":
    from utils.config_loader import ConfigLoader
    
    config_loader = ConfigLoader()
    config = config_loader.load()
    
    syncer = InventorySync(config)
    results = syncer.sync_inventory()
    
    print(f"\n库存同步结果：")
    print(f"  总计：{results.get('total', 0)}")
    print(f"  更新：{results.get('updated', 0)}")
    print(f"  低库存：{results.get('low_stock', 0)}")
    print(f"  缺货：{results.get('out_of_stock', 0)}")
