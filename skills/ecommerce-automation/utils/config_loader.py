"""
配置文件加载器
"""

import os
import yaml
from loguru import logger


class ConfigLoader:
    """配置文件加载器"""

    def __init__(self, config_file="config.yaml"):
        """
        初始化配置加载器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = {}

    def load(self):
        """
        加载配置文件
        
        Returns:
            dict: 配置字典
        """
        try:
            # 尝试多个可能的路径
            possible_paths = [
                self.config_file,
                os.path.join(os.path.dirname(__file__), "..", self.config_file),
                os.path.join(os.getcwd(), self.config_file),
            ]
            
            config_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
            
            if not config_path:
                logger.warning(f"配置文件不存在：{self.config_file}, 使用默认配置")
                return self._get_default_config()
            
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"配置文件已加载：{config_path}")
            
            # 合并默认配置
            default_config = self._get_default_config()
            self._merge_configs(default_config)
            
            return self.config
            
        except Exception as e:
            logger.error(f"加载配置文件失败：{e}")
            return self._get_default_config()

    def _get_default_config(self):
        """获取默认配置"""
        return {
            "basic": {
                "name": "1688 选品 + 拼多多运营自动化",
                "version": "1.0.0",
                "data_dir": "./data",
                "logs_dir": "./logs",
                "log_level": "INFO"
            },
            "source_1688": {
                "mode": "hybrid",
                "browser": {
                    "type": "edge",
                    "headless": False,
                    "port": 9222,
                    "user_data_dir": "./browser_data/1688"
                },
                "selection": {
                    "min_profit_margin": 30,
                    "min_sales": 100,
                    "min_chengxintong_years": 2,
                    "min_repeat_rate": 20,
                    "batch_size": 50,
                    "keywords": ["居家日用", "收纳整理", "厨房用品"]
                }
            },
            "platform_pdd": {
                "mode": "hybrid",
                "browser": {
                    "type": "edge",
                    "headless": False,
                    "port": 9223,
                    "user_data_dir": "./browser_data/pdd"
                },
                "shops": [
                    {
                        "shop_id": "shop_001",
                        "shop_name": "店铺 A",
                        "username": "",
                        "password": "",
                        "status": "active"
                    }
                ],
                "listing": {
                    "auto_optimize_title": True,
                    "title_prefix": "",
                    "title_suffix": "包邮 正品 热销",
                    "default_ship_from": "广东广州",
                    "stock_warning_threshold": 10,
                    "pricing_strategy": "fixed",
                    "fixed_markup_rate": 0.5
                }
            },
            "order_processing": {
                "check_interval": 300,
                "auto_confirm": False,
                "auto_purchase": False,
                "export_format": "excel",
                "retention_days": 90
            },
            "inventory_sync": {
                "enabled": True,
                "sync_interval": 1800,
                "safety_stock": 5,
                "low_stock_alert": True,
                "low_stock_threshold": 20
            },
            "reports": {
                "daily_report": True,
                "daily_report_time": "23:00",
                "notify_method": "dingtalk",
                "dingtalk_webhook": ""
            },
            "compliance": {
                "forbidden_words_check": True,
                "advertising_law_check": True,
                "action_delay": 3,
                "max_daily_listings": 100,
                "max_retries": 3,
                "retry_delay": 60
            },
            "scheduler": {
                "enabled": True,
                "timezone": "Asia/Shanghai",
                "tasks": []
            }
        }

    def _merge_configs(self, default_config):
        """
        合并配置（默认配置作为基础，用户配置覆盖）
        
        Args:
            default_config: 默认配置字典
        """
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value
            elif isinstance(value, dict) and isinstance(self.config[key], dict):
                # 递归合并子字典
                for sub_key, sub_value in value.items():
                    if sub_key not in self.config[key]:
                        self.config[key][sub_key] = sub_value

    def get(self, key, default=None):
        """
        获取配置值
        
        Args:
            key: 配置键（支持嵌套，如 "basic.name"）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    def save(self, config_file=None):
        """
        保存配置到文件
        
        Args:
            config_file: 保存路径，如果为 None 则使用原路径
        """
        save_path = config_file or self.config_file
        
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            
            logger.info(f"配置已保存：{save_path}")
            
        except Exception as e:
            logger.error(f"保存配置失败：{e}")


if __name__ == "__main__":
    # 测试
    loader = ConfigLoader()
    config = loader.load()
    
    print("\n=== 配置加载测试 ===\n")
    print(f"技能名称：{config.get('basic', {}).get('name')}")
    print(f"选品模式：{config.get('source_1688', {}).get('mode')}")
    print(f"店铺数量：{len(config.get('platform_pdd', {}).get('shops', []))}")
