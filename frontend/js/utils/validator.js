/**
 * 表单验证工具模块
 */
const Validator = {
    // 验证规则
    rules: {
        required: (value) => value !== '' && value !== null && value !== undefined,
        email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
        phone: (value) => /^1[3-9]\d{9}$/.test(value),
        minLength: (value, len) => value && value.length >= len,
        maxLength: (value, len) => !value || value.length <= len,
        min: (value, minVal) => !isNaN(value) && Number(value) >= minVal,
        max: (value, maxVal) => !isNaN(value) && Number(value) <= maxVal,
        pattern: (value, regex) => regex.test(value),
        url: (value) => /^https?:\/\/.+/.test(value),
        number: (value) => !isNaN(value) && value !== '',
        integer: (value) => /^\d+$/.test(value)
    },

    // 错误消息
    messages: {
        required: '此字段为必填项',
        email: '请输入有效的邮箱地址',
        phone: '请输入有效的手机号码',
        minLength: '最少需要{0}个字符',
        maxLength: '最多允许{0}个字符',
        min: '最小值为{0}',
        max: '最大值为{0}',
        pattern: '格式不正确',
        url: '请输入有效的URL地址',
        number: '请输入数字',
        integer: '请输入整数'
    },

    /**
     * 验证单个字段
     * @param {*} value - 字段值
     * {Array} rules - 验证规则
     * @returns {Object}
     */
    validateField(value, rules) {
        for (const rule of rules) {
            let ruleName, ruleParam;

            if (typeof rule === 'string') {
                ruleName = rule;
                ruleParam = null;
            } else if (typeof rule === 'object') {
                ruleName = rule.name;
                ruleParam = rule.param;
            } else {
                continue;
            }

            const validateFunc = this.rules[ruleName];
            if (!validateFunc) continue;

            let isValid;
            try {
                isValid = ruleParam !== null
                    ? validateFunc(value, ruleParam)
                    : validateFunc(value);
            } catch (error) {
                isValid = false;
            }

            if (!isValid) {
                let message = this.messages[ruleName] || '验证失败';
                if (ruleParam !== null) {
                    message = message.replace('{0}', ruleParam);
                }
                return { valid: false, message };
            }
        }
        return { valid: true };
    },

    /**
     * 验证整个表单
     * @param {Object} formData - 表单数据
     * @param {Object} schema - 验证规则
     * @returns {Object}
     */
    validateForm(formData, schema) {
        const errors = {};
        let isValid = true;

        for (const [field, rules] of Object.entries(schema)) {
            const value = formData[field];
            const result = this.validateField(value, rules);

            if (!result.valid) {
                errors[field] = result.message;
                isValid = false;
            }
        }

        return { valid: isValid, errors };
    },

    /**
     * 清理输入，防止XSS
     * @param {string} text - 输入文本
     * @returns {string}
     */
    sanitize(text) {
        if (!text) return text;

        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * 清理对象中的字符串值
     * @param {Object} obj - 输入对象
     * @returns {Object}
     */
    sanitizeObject(obj) {
        const result = {};
        for (const [key, value] of Object.entries(obj)) {
            if (typeof value === 'string') {
                result[key] = this.sanitize(value);
            } else if (typeof value === 'object' && value !== null) {
                result[key] = this.sanitizeObject(value);
            } else {
                result[key] = value;
            }
        }
        return result;
    }
};

// 全局可用
window.Validator = Validator;
