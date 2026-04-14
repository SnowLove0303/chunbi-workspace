"""
数据报表生成模块

功能：
1. 自动生成销售日报/周报/月报
2. 商品销量排行分析
3. 利润统计
4. 竞品监控报告
5. 报表推送（钉钉/邮件）
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.excel_handler import ExcelHandler


class ReportGenerator:
    """报表生成器"""

    def __init__(self, config):
        """
        初始化报表生成器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.reports_config = config.get("reports", {})
        
        # 数据存储路径
        self.data_dir = os.path.join(
            config.get("basic", {}).get("data_dir", "./data"),
            "reports"
        )
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 订单和商品数据路径
        self.orders_dir = os.path.join(
            config.get("basic", {}).get("data_dir", "./data"),
            "orders"
        )
        self.products_dir = os.path.join(
            config.get("basic", {}).get("data_dir", "./data"),
            "products"
        )
        
        logger.info("报表生成模块初始化完成")

    def generate_daily_report(self, date=None):
        """
        生成销售日报
        
        Args:
            date: 日期 (YYYY-MM-DD), 默认为昨天
            
        Returns:
            str: 报表文件路径
        """
        if date is None:
            # 默认为昨天
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        logger.info(f"开始生成 {date} 的销售日报...")
        
        report_data = {
            "date": date,
            "summary": {},
            "top_products": [],
            "profit_analysis": {},
            "issues": []
        }
        
        try:
            # 加载订单数据
            orders_df = self._load_orders_by_date(date)
            
            if orders_df is None or orders_df.empty:
                logger.warning(f"{date} 没有订单数据")
                report_data["issues"].append(f"{date} 无订单数据")
            else:
                # 销售汇总
                report_data["summary"] = self._calculate_sales_summary(orders_df)
                
                # 商品销量排行
                report_data["top_products"] = self._analyze_product_sales(orders_df)
                
                # 利润分析
                report_data["profit_analysis"] = self._analyze_profit(orders_df)
            
            # 加载商品数据
            products_df = self._load_latest_products()
            if products_df is not None and not products_df.empty:
                # 库存预警
                low_stock_items = self._check_low_stock(products_df)
                if low_stock_items:
                    report_data["issues"].extend(low_stock_items)
            
            # 生成报表文件
            filepath = self._create_report_file(report_data, "daily")
            
            logger.info(f"日报已生成：{filepath}")
            
            # 推送通知
            if self.reports_config.get("notify_method") == "dingtalk":
                self._send_dingtalk_notification(report_data, "daily")
            
            return filepath
            
        except Exception as e:
            logger.error(f"生成日报失败：{e}")
            return None

    def generate_weekly_report(self, end_date=None):
        """
        生成周报
        
        Args:
            end_date: 结束日期 (YYYY-MM-DD), 默认为昨天
            
        Returns:
            str: 报表文件路径
        """
        if end_date is None:
            end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        start_dt = end_dt - timedelta(days=6)  # 往前推 7 天
        
        start_date = start_dt.strftime("%Y-%m-%d")
        
        logger.info(f"开始生成周报 ({start_date} ~ {end_date})...")
        
        report_data = {
            "period": f"{start_date} ~ {end_date}",
            "summary": {},
            "trend_analysis": [],
            "top_products": [],
            "issues": []
        }
        
        try:
            # 加载订单数据
            orders_df = self._load_orders_by_date_range(start_date, end_date)
            
            if orders_df is None or orders_df.empty:
                logger.warning("该周期内没有订单数据")
            else:
                # 销售汇总
                report_data["summary"] = self._calculate_sales_summary(orders_df)
                
                # 趋势分析（按天）
                report_data["trend_analysis"] = self._analyze_daily_trend(orders_df)
                
                # 商品排行
                report_data["top_products"] = self._analyze_product_sales(orders_df, top_n=10)
            
            # 生成报表
            filepath = self._create_report_file(report_data, "weekly")
            
            logger.info(f"周报已生成：{filepath}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"生成周报失败：{e}")
            return None

    def generate_monthly_report(self, year_month=None):
        """
        生成月报
        
        Args:
            year_month: 年月 (YYYY-MM), 默认为上月
            
        Returns:
            str: 报表文件路径
        """
        if year_month is None:
            # 默认为上月
            last_month = datetime.now().replace(day=1) - timedelta(days=1)
            year_month = last_month.strftime("%Y-%m")
        
        logger.info(f"开始生成 {year_month} 的月报...")
        
        # 计算该月的起止日期
        start_date = f"{year_month}-01"
        if year_month == datetime.now().strftime("%Y-%m"):
            end_date = datetime.now().strftime("%Y-%m-%d")
        else:
            # 下月第一天减 1
            next_month = datetime.strptime(year_month, "%Y-%m") + timedelta(days=32)
            next_month = next_month.replace(day=1)
            end_date = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")
        
        report_data = {
            "period": f"{year_month}",
            "summary": {},
            "monthly_comparison": [],
            "product_analysis": [],
            "recommendations": []
        }
        
        try:
            # 加载订单数据
            orders_df = self._load_orders_by_date_range(start_date, end_date)
            
            if orders_df is not None and not orders_df.empty:
                # 月度销售汇总
                report_data["summary"] = self._calculate_sales_summary(orders_df)
                
                # 商品分析
                report_data["product_analysis"] = self._analyze_product_sales(orders_df, top_n=20)
                
                # 生成经营建议
                report_data["recommendations"] = self._generate_recommendations(orders_df)
            
            # 生成报表
            filepath = self._create_report_file(report_data, "monthly")
            
            logger.info(f"月报已生成：{filepath}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"生成月报失败：{e}")
            return None

    def _load_orders_by_date(self, date):
        """加载指定日期的订单数据"""
        try:
            files = os.listdir(self.orders_dir)
            order_files = [f for f in files if f.startswith("订单数据") and f.endswith(".xlsx")]
            
            all_orders = []
            for file in order_files:
                filepath = os.path.join(self.orders_dir, file)
                df = pd.read_excel(filepath)
                
                # 筛选日期
                if "process_time" in df.columns:
                    df = df[df["process_time"].str.startswith(date)]
                
                if not df.empty:
                    all_orders.append(df)
            
            if all_orders:
                return pd.concat(all_orders, ignore_index=True)
            return None
            
        except Exception as e:
            logger.error(f"加载订单数据失败：{e}")
            return None

    def _load_orders_by_date_range(self, start_date, end_date):
        """加载日期范围内的订单数据"""
        try:
            files = os.listdir(self.orders_dir)
            order_files = [f for f in files if f.startswith("订单数据") and f.endswith(".xlsx")]
            
            all_orders = []
            for file in order_files:
                filepath = os.path.join(self.orders_dir, file)
                df = pd.read_excel(filepath)
                
                # 筛选日期范围
                if "process_time" in df.columns:
                    df = df[(df["process_time"] >= start_date) & (df["process_time"] <= end_date)]
                
                if not df.empty:
                    all_orders.append(df)
            
            if all_orders:
                return pd.concat(all_orders, ignore_index=True)
            return None
            
        except Exception as e:
            logger.error(f"加载订单数据失败：{e}")
            return None

    def _load_latest_products(self):
        """加载最新的商品数据"""
        try:
            files = os.listdir(self.products_dir)
            xlsx_files = [f for f in files if f.startswith("1688 选品") and f.endswith(".xlsx")]
            
            if not xlsx_files:
                return None
            
            latest_file = sorted(xlsx_files)[-1]
            filepath = os.path.join(self.products_dir, latest_file)
            
            return pd.read_excel(filepath)
            
        except Exception as e:
            logger.error(f"加载商品数据失败：{e}")
            return None

    def _calculate_sales_summary(self, orders_df):
        """
        计算销售汇总
        
        Args:
            orders_df: 订单数据
            
        Returns:
            dict: 销售汇总指标
        """
        summary = {}
        
        try:
            # 订单数
            summary["total_orders"] = len(orders_df)
            
            # 销售额（如果有价格字段）
            if "price" in orders_df.columns:
                summary["total_sales"] = orders_df["price"].sum()
                summary["avg_order_value"] = orders_df["price"].mean()
            
            # 商品数量
            if "quantity" in orders_df.columns:
                summary["total_items"] = orders_df["quantity"].sum()
            
            # 买家数
            if "buyer_nickname" in orders_df.columns:
                summary["unique_buyers"] = orders_df["buyer_nickname"].nunique()
            
        except Exception as e:
            logger.warning(f"计算销售汇总时出错：{e}")
        
        return summary

    def _analyze_product_sales(self, orders_df, top_n=5):
        """
        分析商品销量排行
        
        Args:
            orders_df: 订单数据
            top_n: 返回前 N 个商品
            
        Returns:
            list: 商品销量排行列表
        """
        try:
            if "goods_name" not in orders_df.columns:
                return []
            
            # 按商品分组统计
            product_stats = orders_df.groupby("goods_name").agg({
                "order_sn": "count",  # 订单数
                "quantity": "sum",    # 销量
                "price": "sum"        # 销售额
            }).reset_index()
            
            product_stats.columns = ["商品名称", "订单数", "销量", "销售额"]
            
            # 按销量排序
            product_stats = product_stats.sort_values("销量", ascending=False)
            
            # 取 Top N
            top_products = product_stats.head(top_n).to_dict("records")
            
            return top_products
            
        except Exception as e:
            logger.error(f"分析商品销量失败：{e}")
            return []

    def _analyze_profit(self, orders_df):
        """
        分析利润
        
        Args:
            orders_df: 订单数据
            
        Returns:
            dict: 利润分析结果
        """
        profit_analysis = {}
        
        try:
            # 如果有利润字段
            if "net_profit" in orders_df.columns:
                profit_analysis["total_profit"] = orders_df["net_profit"].sum()
                profit_analysis["avg_profit_margin"] = orders_df.get("profit_margin", pd.Series()).mean()
            
            # 按商品分析利润
            if "goods_name" in orders_df.columns and "net_profit" in orders_df.columns:
                product_profit = orders_df.groupby("goods_name")["net_profit"].sum()
                top_profit_product = product_profit.idxmax() if not product_profit.empty else None
                profit_analysis["top_profit_product"] = top_profit_product
            
        except Exception as e:
            logger.warning(f"分析利润时出错：{e}")
        
        return profit_analysis

    def _analyze_daily_trend(self, orders_df):
        """
        分析每日销售趋势
        
        Args:
            orders_df: 订单数据
            
        Returns:
            list: 每日趋势数据
        """
        try:
            if "process_time" not in orders_df.columns:
                return []
            
            # 按日期分组
            orders_df["date"] = orders_df["process_time"].str[:10]
            
            daily_stats = orders_df.groupby("date").agg({
                "order_sn": "count",
                "price": "sum"
            }).reset_index()
            
            daily_stats.columns = ["日期", "订单数", "销售额"]
            
            return daily_stats.to_dict("records")
            
        except Exception as e:
            logger.error(f"分析趋势失败：{e}")
            return []

    def _check_low_stock(self, products_df):
        """
        检查低库存商品
        
        Args:
            products_df: 商品数据
            
        Returns:
            list: 低库存商品列表
        """
        issues = []
        
        try:
            threshold = self.config.get("inventory_sync", {}).get("low_stock_threshold", 20)
            
            if "available_stock" in products_df.columns:
                low_stock_items = products_df[products_df["available_stock"] < threshold]
                
                for _, row in low_stock_items.iterrows():
                    title = row.get("title", "未知商品")
                    stock = row.get("available_stock", 0)
                    issues.append(f"低库存：{title[:30]}... (库存：{stock})")
        
        except Exception as e:
            logger.warning(f"检查库存失败：{e}")
        
        return issues

    def _generate_recommendations(self, orders_df):
        """
        生成经营建议
        
        Args:
            orders_df: 订单数据
            
        Returns:
            list: 建议列表
        """
        recommendations = []
        
        try:
            # 基于销量分析
            if len(orders_df) > 0:
                avg_daily_orders = len(orders_df) / 7  # 假设是周报数据
                
                if avg_daily_orders < 5:
                    recommendations.append("日均订单较少，建议加大推广力度或优化选品")
                elif avg_daily_orders > 20:
                    recommendations.append("订单量良好，可考虑拓展更多商品类目")
            
            # 基于利润分析
            if "profit_margin" in orders_df.columns:
                avg_margin = orders_df["profit_margin"].mean()
                if avg_margin < 20:
                    recommendations.append("毛利率偏低，建议优化定价策略或寻找更优质的供应商")
                elif avg_margin > 50:
                    recommendations.append("毛利率良好，可考虑适当降价以提升销量")
        
        except Exception as e:
            logger.warning(f"生成建议失败：{e}")
        
        return recommendations

    def _create_report_file(self, report_data, report_type):
        """
        创建报表文件
        
        Args:
            report_data: 报表数据字典
            report_type: 报表类型 (daily / weekly / monthly)
            
        Returns:
            str: 文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if report_type == "daily":
            date_str = report_data.get("date", "unknown")
            filename = f"销售日报_{date_str}_{timestamp}.xlsx"
        elif report_type == "weekly":
            period = report_data.get("period", "unknown").replace(" ~ ", "_")
            filename = f"销售周报_{period}_{timestamp}.xlsx"
        else:  # monthly
            period = report_data.get("period", "unknown")
            filename = f"销售月报_{period}_{timestamp}.xlsx"
        
        filepath = os.path.join(self.data_dir, filename)
        
        # 将报表数据转换为 DataFrame 并保存
        df_summary = pd.DataFrame([report_data.get("summary", {})])
        
        excel_handler = ExcelHandler()
        excel_handler.save_to_excel(df_summary, filepath, sheet_name="销售汇总")
        
        # 添加其他工作表
        with pd.ExcelWriter(filepath, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            if report_data.get("top_products"):
                df_products = pd.DataFrame(report_data["top_products"])
                df_products.to_excel(writer, sheet_name="商品排行", index=False)
            
            if report_data.get("trend_analysis"):
                df_trend = pd.DataFrame(report_data["trend_analysis"])
                df_trend.to_excel(writer, sheet_name="趋势分析", index=False)
        
        return filepath

    def _send_dingtalk_notification(self, report_data, report_type):
        """
        发送钉钉通知
        
        Args:
            report_data: 报表数据
            report_type: 报表类型
        """
        webhook = self.reports_config.get("dingtalk_webhook", "")
        
        if not webhook:
            logger.warning("未配置钉钉 Webhook，跳过通知")
            return
        
        try:
            # TODO: 实现钉钉消息发送
            # 可以参考 utils/dingtalk_notify.py
            
            message = f"📊 {report_type.upper()} 已生成\n\n"
            
            summary = report_data.get("summary", {})
            message += f"订单数：{summary.get('total_orders', 0)}\n"
            message += f"销售额：{summary.get('total_sales', 0):.2f}元\n"
            message += f"利润：{report_data.get('profit_analysis', {}).get('total_profit', 0):.2f}元\n"
            
            logger.info(f"钉钉通知内容：{message}")
            # 实际发送逻辑待实现
            
        except Exception as e:
            logger.error(f"发送钉钉通知失败：{e}")


if __name__ == "__main__":
    from utils.config_loader import ConfigLoader
    
    config_loader = ConfigLoader()
    config = config_loader.load()
    
    generator = ReportGenerator(config)
    
    # 生成日报
    filepath = generator.generate_daily_report()
    if filepath:
        print(f"\n日报已生成：{filepath}")
