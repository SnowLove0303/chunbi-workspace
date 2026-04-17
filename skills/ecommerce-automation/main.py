#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
1688 选品 + 拼多多运营自动化技能 - 主程序入口

功能：
1. 1688 智能选品
2. 拼多多商品上架
3. 订单自动处理
4. 库存同步管理
5. 数据报表生成
6. 合规检测

使用方法：
    python main.py --help              # 查看帮助
    python main.py select              # 执行 1688 选品
    python main.py publish             # 发布商品到拼多多
    python main.py orders              # 处理订单
    python main.py sync                # 同步库存
    python main.py report              # 生成报表
    python main.py all                 # 执行全流程

作者：AI 团队
版本：1.0.0
"""

import os
import sys
import argparse
import time
from datetime import datetime
from loguru import logger

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_loader import ConfigLoader
from utils.dingtalk_notify import DingTalkNotifier
from modules.selector_1688 import Selector1688
from modules.publisher_pdd import PublisherPDD
from modules.order_processor import OrderProcessor
from modules.inventory_sync import InventorySync
from modules.report_generator import ReportGenerator
from modules.compliance_check import ComplianceCheck


def setup_logger(log_dir="./logs", log_level="INFO"):
    """配置日志"""
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"电商运营_{datetime.now().strftime('%Y%m%d')}.log")
    
    logger.remove()  # 移除默认处理器
    
    # 控制台输出
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
    )
    
    # 文件输出
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
        rotation="1 day",
        retention="30 days",
        encoding="utf-8"
    )
    
    logger.info("日志系统初始化完成")


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║       1688 选品 + 拼多多运营自动化技能 v1.0.0              ║
║                                                           ║
║       功能：智能选品 | 一键上架 | 订单处理 | 库存同步      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_selection(config, keywords=None):
    """执行 1688 选品"""
    logger.info("=" * 60)
    logger.info("开始执行 1688 选品流程")
    logger.info("=" * 60)
    
    try:
        selector = Selector1688(config)
        df = selector.select_products(keywords=keywords)
        
        if df is not None and not df.empty:
            logger.info(f"✅ 选品完成！共采集 {len(df)} 个商品")
            
            # 显示前 5 个商品预览
            print("\n=== 选品结果预览 ===")
            preview_cols = ["title", "price", "sales", "suggested_price", "profit_margin"]
            available_cols = [col for col in preview_cols if col in df.columns]
            print(df[available_cols].head())
            
            return True
        else:
            logger.warning("⚠️ 未采集到任何商品")
            return False
            
    except Exception as e:
        logger.error(f"❌ 选品失败：{e}")
        return False


def run_publishing(config, shop_id=None):
    """执行拼多多商品上架"""
    logger.info("=" * 60)
    logger.info("开始执行拼多多商品上架流程")
    logger.info("=" * 60)
    
    try:
        publisher = PublisherPDD(config)
        
        # 显示可用店铺
        print("\n=== 可用店铺 ===")
        for shop in publisher.list_shops():
            status = "✓" if shop.get("status") == "active" else "✗"
            print(f"  {status} {shop['shop_name']} ({shop['shop_id']})")
        
        results = publisher.publish_products(shop_id=shop_id)
        
        if results.get("success", 0) > 0:
            logger.info(f"✅ 上架完成！成功 {results['success']} 个，失败 {results['failed']} 个")
            return True
        else:
            logger.warning("⚠️ 没有成功上架任何商品")
            return False
            
    except Exception as e:
        logger.error(f"❌ 上架失败：{e}")
        return False


def run_order_processing(config, auto_purchase=False):
    """执行订单处理"""
    logger.info("=" * 60)
    logger.info("开始执行订单处理流程")
    logger.info("=" * 60)
    
    try:
        processor = OrderProcessor(config)
        results = processor.process_orders(auto_purchase=auto_purchase)
        
        if "error" not in results:
            logger.info(f"✅ 订单处理完成！")
            logger.info(f"  总计：{results.get('total', 0)}")
            logger.info(f"  已确认：{results.get('confirmed', 0)}")
            logger.info(f"  待处理：{results.get('pending', 0)}")
            logger.info(f"  异常：{results.get('abnormal', 0)}")
            return True
        else:
            logger.error(f"❌ 订单处理失败：{results.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 订单处理失败：{e}")
        return False


def run_inventory_sync(config):
    """执行库存同步"""
    logger.info("=" * 60)
    logger.info("开始执行库存同步流程")
    logger.info("=" * 60)
    
    try:
        syncer = InventorySync(config)
        results = syncer.sync_inventory()
        
        if results.get("status") != "disabled":
            logger.info(f"✅ 库存同步完成！")
            logger.info(f"  总计：{results.get('total', 0)}")
            logger.info(f"  更新：{results.get('updated', 0)}")
            logger.info(f"  低库存：{results.get('low_stock', 0)}")
            logger.info(f"  缺货：{results.get('out_of_stock', 0)}")
            return True
        else:
            logger.info("ℹ️ 库存同步功能已禁用")
            return True
            
    except Exception as e:
        logger.error(f"❌ 库存同步失败：{e}")
        return False


def run_report_generation(config, report_type="daily"):
    """生成数据报表"""
    logger.info("=" * 60)
    logger.info(f"开始生成{report_type}报表")
    logger.info("=" * 60)
    
    try:
        generator = ReportGenerator(config)
        
        if report_type == "daily":
            filepath = generator.generate_daily_report()
        elif report_type == "weekly":
            filepath = generator.generate_weekly_report()
        elif report_type == "monthly":
            filepath = generator.generate_monthly_report()
        else:
            logger.error(f"未知的报表类型：{report_type}")
            return False
        
        if filepath:
            logger.info(f"✅ 报表已生成：{filepath}")
            return True
        else:
            logger.warning("⚠️ 报表生成失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 报表生成失败：{e}")
        return False


def run_compliance_check(config):
    """执行合规检测"""
    logger.info("=" * 60)
    logger.info("开始执行商品合规检测")
    logger.info("=" * 60)
    
    try:
        checker = ComplianceCheck(config)
        
        # 加载商品数据
        from modules.selector_1688 import Selector1688
        selector = Selector1688(config)
        products_df = selector._load_local_products()
        
        if products_df is None or products_df.empty:
            logger.warning("⚠️ 没有可检测的商品数据")
            return False
        
        # 执行检测
        report_df = checker.generate_compliance_report(products_df)
        
        compliant_count = report_df["is_compliant"].sum()
        total_count = len(report_df)
        
        logger.info(f"✅ 合规检测完成！")
        logger.info(f"  合规商品：{compliant_count}/{total_count}")
        logger.info(f"  不合规商品：{total_count - compliant_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 合规检测失败：{e}")
        return False


def run_all(config):
    """执行全流程"""
    logger.info("\n" + "=" * 60)
    logger.info("开始执行全流程自动化运营")
    logger.info("=" * 60 + "\n")
    
    results = {}
    
    # 1. 选品
    logger.info("【步骤 1/5】1688 选品")
    results["selection"] = run_selection(config)
    time.sleep(2)
    
    # 2. 合规检测
    logger.info("\n【步骤 2/5】商品合规检测")
    results["compliance"] = run_compliance_check(config)
    time.sleep(2)
    
    # 3. 上架
    logger.info("\n【步骤 3/5】拼多多商品上架")
    results["publishing"] = run_publishing(config)
    time.sleep(2)
    
    # 4. 订单处理
    logger.info("\n【步骤 4/5】订单处理")
    results["orders"] = run_order_processing(config)
    time.sleep(2)
    
    # 5. 库存同步
    logger.info("\n【步骤 5/5】库存同步")
    results["inventory"] = run_inventory_sync(config)
    time.sleep(2)
    
    # 生成报表
    logger.info("\n【附加步骤】生成日报")
    results["report"] = run_report_generation(config, report_type="daily")
    
    # 汇总结果
    logger.info("\n" + "=" * 60)
    logger.info("全流程执行完毕！结果汇总：")
    logger.info("=" * 60)
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for step, result in results.items():
        status = "✅" if result else "❌"
        logger.info(f"  {status} {step}: {'成功' if result else '失败'}")
    
    logger.info(f"\n总体成功率：{success_count}/{total_count}")
    
    return success_count == total_count


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="1688 选品 + 拼多多运营自动化技能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py select                    # 执行 1688 选品
  python main.py publish --shop shop_001   # 发布商品到指定店铺
  python main.py orders --auto-purchase    # 处理订单并自动采购
  python main.py report --type weekly      # 生成周报
  python main.py all                       # 执行全流程
        """
    )
    
    parser.add_argument(
        "command",
        choices=["select", "publish", "orders", "sync", "report", "compliance", "all"],
        help="要执行的命令"
    )
    
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="配置文件路径 (默认：config.yaml)"
    )
    
    parser.add_argument(
        "--shop", "-s",
        default=None,
        help="店铺 ID (用于发布命令)"
    )
    
    parser.add_argument(
        "--keywords", "-k",
        nargs="+",
        default=None,
        help="选品关键词列表 (用于选品命令)"
    )
    
    parser.add_argument(
        "--auto-purchase",
        action="store_true",
        help="是否自动采购 (用于订单命令)"
    )
    
    parser.add_argument(
        "--type", "-t",
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="报表类型 (用于报表命令)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别"
    )
    
    args = parser.parse_args()
    
    # 打印欢迎横幅
    print_banner()
    
    # 加载配置
    config_loader = ConfigLoader(config_file=args.config)
    config = config_loader.load()
    
    # 配置日志
    log_dir = config.get("basic", {}).get("logs_dir", "./logs")
    setup_logger(log_dir=log_dir, log_level=args.log_level)
    
    logger.info(f"配置已加载：{args.config}")
    logger.info(f"执行命令：{args.command}")
    
    # 执行对应命令
    success = False
    
    if args.command == "select":
        success = run_selection(config, keywords=args.keywords)
    
    elif args.command == "publish":
        success = run_publishing(config, shop_id=args.shop)
    
    elif args.command == "orders":
        success = run_order_processing(config, auto_purchase=args.auto_purchase)
    
    elif args.command == "sync":
        success = run_inventory_sync(config)
    
    elif args.command == "report":
        success = run_report_generation(config, report_type=args.type)
    
    elif args.command == "compliance":
        success = run_compliance_check(config)
    
    elif args.command == "all":
        success = run_all(config)
    
    # 退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
