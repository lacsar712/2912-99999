"""
数据验证工具
"""
import re
from typing import Dict, List, Any, Optional
from datetime import datetime


class Validator:
    """数据验证工具类"""

    # 验证规则
    rules = {
        'required': lambda value: value is not None and value != '',
        'email': lambda value: re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', str(value)) is not None,
        'phone': lambda value: re.match(r'^1[3-9]\d{9}$', str(value)) is not None,
        'min_length': lambda value, min_len: len(str(value)) >= min_len,
        'max_length': lambda value, max_len: len(str(value)) <= max_len,
        'min_value': lambda value, min_val: float(value) >= min_val,
        'max_value': lambda value, max_val: float(value) <= max_val,
        'pattern': lambda value, regex: re.match(regex, str(value)) is not None,
        'integer': lambda value: isinstance(value, int) or str(value).isdigit(),
        'positive': lambda value: float(value) > 0,
        'date': lambda value: Validator._is_valid_date(value),
    }

    # 错误消息
    messages = {
        'required': '此字段为必填项',
        'email': '请输入有效的邮箱地址',
        'phone': '请输入有效的手机号码',
        'min_length': '最少需要{0}个字符',
        'max_length': '最多允许{0}个字符',
        'min_value': '最小值为{0}',
        'max_value': '最大值为{0}',
        'pattern': '格式不正确',
        'integer': '必须是整数',
        'positive': '必须是正数',
        'date': '日期格式不正确，请使用YYYY-MM-DD格式',
    }

    @staticmethod
    def _is_valid_date(value: str) -> bool:
        """验证日期格式"""
        try:
            datetime.strptime(str(value), '%Y-%m-%d')
            return True
        except (ValueError, TypeError):
            return False

    @classmethod
    def validate_field(cls, value: Any, rules: List) -> Dict[str, Any]:
        """
        验证单个字段

        Args:
            value: 字段值
            rules: 验证规则列表

        Returns:
            验证结果
        """
        for rule in rules:
            if isinstance(rule, str):
                rule_name = rule
                rule_param = None
            elif isinstance(rule, dict):
                rule_name = rule.get('name')
                rule_param = rule.get('param')
            else:
                continue

            # 获取验证函数
            validate_func = cls.rules.get(rule_name)
            if not validate_func:
                continue

            # 执行验证
            try:
                if rule_param is not None:
                    is_valid = validate_func(value, rule_param)
                else:
                    is_valid = validate_func(value)

                if not is_valid:
                    message = cls.messages.get(rule_name, '验证失败')
                    if rule_param is not None:
                        message = message.replace('{0}', str(rule_param))
                    return {'valid': False, 'message': message}
            except Exception:
                return {'valid': False, 'message': '验证过程出错'}

        return {'valid': True}

    @classmethod
    def validate_form(cls, data: Dict[str, Any], schema: Dict[str, List]) -> Dict[str, Any]:
        """
        验证整个表单

        Args:
            data: 表单数据
            schema: 验证规则

        Returns:
            验证结果
        """
        errors = {}
        is_valid = True

        for field, rules in schema.items():
            value = data.get(field)
            result = cls.validate_field(value, rules)
            if not result['valid']:
                errors[field] = result['message']
                is_valid = False

        return {'valid': is_valid, 'errors': errors}

    @staticmethod
    def sanitize_string(value: str) -> str:
        """
        清理字符串，防止XSS

        Args:
            value: 输入字符串

        Returns:
            清理后的字符串
        """
        if not value:
            return value

        # 转义特殊字符
        value = value.replace('&', '&amp;')
        value = value.replace('<', '&lt;')
        value = value.replace('>', '&gt;')
        value = value.replace('"', '&quot;')
        value = value.replace("'", '&#x27;')

        return value

    @staticmethod
    def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理字典中的字符串值

        Args:
            data: 输入字典

        Returns:
            清理后的字典
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = Validator.sanitize_string(value)
            elif isinstance(value, dict):
                result[key] = Validator.sanitize_dict(value)
            else:
                result[key] = value
        return result
