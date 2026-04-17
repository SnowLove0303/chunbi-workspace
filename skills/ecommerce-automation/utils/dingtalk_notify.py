"""
钉钉通知工具

功能：
1. 发送文本消息
2. 发送 Markdown 消息
3. 发送文件
4. 定时推送报表
"""

import os
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
from datetime import datetime
from loguru import logger


class DingTalkNotifier:
    """钉钉通知器"""

    def __init__(self, webhook_url, secret=None):
        """
        初始化钉钉通知器
        
        Args:
            webhook_url: 钉钉机器人 Webhook URL
            secret: 加签密钥（可选）
        """
        self.webhook_url = webhook_url
        self.secret = secret

    def send_text(self, content, at_all=False, at_mobiles=None):
        """
        发送文本消息
        
        Args:
            content: 消息内容
            at_all: 是否@所有人
            at_mobiles: 需要@的手机号列表
            
        Returns:
            bool: 是否发送成功
        """
        if not self.webhook_url:
            logger.warning("未配置钉钉 Webhook")
            return False
        
        try:
            data = {
                "msgtype": "text",
                "text": {
                    "content": content
                },
                "at": {
                    "isAtAll": at_all,
                    "atMobiles": at_mobiles or []
                }
            }
            
            result = self._send_request(data)
            
            if result and result.get("errcode") == 0:
                logger.info("钉钉消息发送成功")
                return True
            else:
                logger.error(f"钉钉消息发送失败：{result}")
                return False
                
        except Exception as e:
            logger.error(f"发送钉钉消息失败：{e}")
            return False

    def send_markdown(self, title, text, at_all=False, at_mobiles=None):
        """
        发送 Markdown 消息
        
        Args:
            title: 消息标题
            text: Markdown 格式的消息内容
            at_all: 是否@所有人
            at_mobiles: 需要@的手机号列表
            
        Returns:
            bool: 是否发送成功
        """
        if not self.webhook_url:
            logger.warning("未配置钉钉 Webhook")
            return False
        
        try:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": text
                },
                "at": {
                    "isAtAll": at_all,
                    "atMobiles": at_mobiles or []
                }
            }
            
            result = self._send_request(data)
            
            if result and result.get("errcode") == 0:
                logger.info("钉钉 Markdown 消息发送成功")
                return True
            else:
                logger.error(f"钉钉 Markdown 消息发送失败：{result}")
                return False
                
        except Exception as e:
            logger.error(f"发送钉钉 Markdown 消息失败：{e}")
            return False

    def send_link(self, title, text, pic_url, message_url):
        """
        发送链接消息
        
        Args:
            title: 消息标题
            text: 消息描述
            pic_url: 图片 URL
            message_url: 点击跳转的 URL
            
        Returns:
            bool: 是否发送成功
        """
        if not self.webhook_url:
            logger.warning("未配置钉钉 Webhook")
            return False
        
        try:
            data = {
                "msgtype": "link",
                "link": {
                    "title": title,
                    "text": text,
                    "picUrl": pic_url,
                    "messageUrl": message_url
                }
            }
            
            result = self._send_request(data)
            
            if result and result.get("errcode") == 0:
                logger.info("钉钉链接消息发送成功")
                return True
            else:
                logger.error(f"钉钉链接消息发送失败：{result}")
                return False
                
        except Exception as e:
            logger.error(f"发送钉钉链接消息失败：{e}")
            return False

    def send_file(self, file_path):
        """
        发送文件消息（需要先上传到钉钉媒体库）
        
        Args:
            file_path: 本地文件路径
            
        Returns:
            bool: 是否发送成功
        """
        # TODO: 实现文件上传和发送逻辑
        logger.warning("文件消息发送功能待实现")
        return False

    def _send_request(self, data):
        """
        发送 HTTP 请求到钉钉
        
        Args:
            data: 请求数据
            
        Returns:
            dict: 响应数据
        """
        # 添加签名（如果配置了 secret）
        url = self.webhook_url
        if self.secret:
            timestamp = str(round(time.time() * 1000))
            sign_string = f"{timestamp}\n{self.secret}"
            sign_code = hmac.new(
                self.secret.encode("utf-8"),
                sign_string.encode("utf-8"),
                digestmod=hashlib.sha256
            ).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(sign_code))
            url = f"{url}&timestamp={timestamp}&sign={sign}"
        
        # 发送请求
        headers = {"Content-Type": "application/json; charset=utf-8"}
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        return response.json()

    def send_sales_report(self, report_data, report_type="daily"):
        """
        发送销售报表
        
        Args:
            report_data: 报表数据字典
            report_type: 报表类型 (daily / weekly / monthly)
            
        Returns:
            bool: 是否发送成功
        """
        summary = report_data.get("summary", {})
        
        # 构建 Markdown 消息
        if report_type == "daily":
            title = "📊 销售日报"
            date_str = report_data.get("date", "今日")
        elif report_type == "weekly":
            title = "📈 销售周报"
            date_str = report_data.get("period", "本周")
        else:
            title = "💰 销售月报"
            date_str = report_data.get("period", "本月")
        
        text = f"## {title}\n\n"
        text += f"**统计周期**: {date_str}\n\n"
        text += "### 核心指标\n"
        text += f"- 📦 订单数：{summary.get('total_orders', 0)}\n"
        text += f"- 💵 销售额：{summary.get('total_sales', 0):.2f}元\n"
        
        if "avg_order_value" in summary:
            text += f"- 📊 客单价：{summary.get('avg_order_value', 0):.2f}元\n"
        
        profit_analysis = report_data.get("profit_analysis", {})
        if "total_profit" in profit_analysis:
            text += f"- 💰 利润：{profit_analysis.get('total_profit', 0):.2f}元\n"
        
        # 商品排行
        top_products = report_data.get("top_products", [])
        if top_products:
            text += "\n### 🔥 热销商品 TOP5\n"
            for i, product in enumerate(top_products[:5], 1):
                product_name = product.get("商品名称", "未知")
                sales = product.get("销量", 0)
                text += f"{i}. {product_name} - 销量：{sales}\n"
        
        # 问题提醒
        issues = report_data.get("issues", [])
        if issues:
            text += "\n### ⚠️ 需要关注\n"
            for issue in issues[:3]:
                text += f"- {issue}\n"
        
        text += f"\n_生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        
        return self.send_markdown(title, text, at_all=False)

    def send_low_stock_alert(self, product_name, current_stock, threshold):
        """
        发送低库存预警
        
        Args:
            product_name: 商品名称
            current_stock: 当前库存
            threshold: 预警阈值
            
        Returns:
            bool: 是否发送成功
        """
        title = "⚠️ 低库存预警"
        text = f"## {title}\n\n"
        text += f"**商品**: {product_name}\n\n"
        text += f"- 当前库存：{current_stock}\n"
        text += f"- 预警阈值：{threshold}\n\n"
        text += "请及时补货！\n\n"
        text += f"_预警时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        
        return self.send_markdown(title, text, at_all=False)

    def send_order_notification(self, order_count, total_amount):
        """
        发送订单通知
        
        Args:
            order_count: 订单数量
            total_amount: 订单总金额
            
        Returns:
            bool: 是否发送成功
        """
        content = f"📢 新订单提醒\n\n"
        content += f"新增订单：{order_count}笔\n"
        content += f"订单金额：{total_amount:.2f}元\n\n"
        content += f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_text(content, at_all=False)


if __name__ == "__main__":
    # 测试
    print("\n=== 钉钉通知测试 ===\n")
    
    # 示例 Webhook（请替换为真实的）
    test_webhook = ""
    test_secret = ""
    
    if test_webhook:
        notifier = DingTalkNotifier(test_webhook, test_secret)
        
        # 测试文本消息
        notifier.send_text("这是一条测试消息")
        
        # 测试 Markdown 消息
        notifier.send_markdown(
            "测试标题",
            "## 测试内容\n\n- 项目 1\n- 项目 2\n- 项目 3"
        )
        
        print("测试完成")
    else:
        print("跳过测试（未配置 Webhook）")
