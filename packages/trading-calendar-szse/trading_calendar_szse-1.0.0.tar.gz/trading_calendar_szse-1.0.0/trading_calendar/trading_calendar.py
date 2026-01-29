import requests
import json
import random
from datetime import datetime, timedelta
import time
import os

class TradingCalendar:
    """深交所交易日历API封装"""
    
    def __init__(self, cache_dir='./cache', cache_expire_hours=24):
        """
        初始化交易日历对象
        
        :param cache_dir: 缓存目录路径
        :param cache_expire_hours: 缓存过期时间（小时）
        """
        self.base_url = "https://www.szse.cn/api/report/exchange/onepersistenthour/monthList"
        self.cache_dir = cache_dir
        self.cache_expire_hours = cache_expire_hours
        
        # 创建缓存目录
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_random_param(self):
        """生成随机参数"""
        return random.random()
    
    def _get_cache_file_path(self, year, month):
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"calendar_{year}_{month:02d}.json")
    
    def _is_cache_valid(self, cache_file):
        """检查缓存是否有效"""
        if not os.path.exists(cache_file):
            return False
        
        # 检查缓存是否过期
        mtime = os.path.getmtime(cache_file)
        now = time.time()
        return (now - mtime) < (self.cache_expire_hours * 3600)
    
    def _get_calendar_data_from_api(self, year, month):
        """从API获取日历数据"""
        params = {
            'random': self._get_random_param()
        }
        
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5',
            'Content-Type': 'application/json',
            'Referer': 'https://www.szse.cn/aboutus/calendar/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = requests.get(self.base_url, params=params, headers=headers)
        response.raise_for_status()  # 抛出HTTP错误
        
        data = response.json()
        
        # 注意：深交所API始终只返回当前月份的数据，不支持查询未来月份
        if 'data' in data and data['data']:
            # 获取API返回数据的实际月份
            first_date = data['data'][0]['jyrq']
            api_month = int(first_date.split('-')[1])
            api_year = int(first_date.split('-')[0])
            
            # 如果请求的月份与API返回的月份不一致，记录日志但不抛出异常
            # 这样可以保持接口的兼容性
            if api_year != year or api_month != month:
                print(f"警告: 请求的是{year}年{month}月，但API只返回当前月份({api_year}年{api_month}月)的数据")
        
        return data
    
    def _save_calendar_data(self, year, month, data):
        """保存日历数据到缓存"""
        cache_file = self._get_cache_file_path(year, month)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_calendar_data(self, year, month):
        """从缓存加载日历数据"""
        cache_file = self._get_cache_file_path(year, month)
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_month_calendar(self, year, month):
        """
        获取指定月份的日历数据
        
        :param year: 年份（如2026）
        :param month: 月份（1-12）
        :return: 日历数据列表
        """
        # 检查缓存
        cache_file = self._get_cache_file_path(year, month)
        if self._is_cache_valid(cache_file):
            try:
                return self._load_calendar_data(year, month)
            except Exception:
                # 缓存文件损坏，删除并重新获取
                if os.path.exists(cache_file):
                    os.remove(cache_file)
        
        # 从API获取数据
        try:
            data = self._get_calendar_data_from_api(year, month)
            # 保存到缓存
            self._save_calendar_data(year, month, data)
            return data
        except Exception as e:
            raise Exception(f"获取日历数据失败: {str(e)}")
    
    def is_trading_day(self, date):
        """
        检查指定日期是否为交易日
        
        :param date: 日期对象或字符串（格式如'2026-01-01'）
        :return: bool - True为交易日，False为非交易日
        """
        # 处理日期参数
        if isinstance(date, str):
            date_obj = datetime.strptime(date, '%Y-%m-%d')
        else:
            date_obj = date
        
        year = date_obj.year
        month = date_obj.month
        date_str = date_obj.strftime('%Y-%m-%d')
        
        # 获取当月日历数据
        calendar_data = self.get_month_calendar(year, month)
        
        # 检查日历数据是否包含请求的日期
        calendar_dates = [day['jyrq'] for day in calendar_data.get('data', [])]
        
        if date_str in calendar_dates:
            # 查找指定日期
            for day in calendar_data.get('data', []):
                if day['jyrq'] == date_str:
                    return day['jybz'] == '1'
        else:
            # 检查API返回数据的日期范围
            if calendar_dates:
                first_date = calendar_dates[0]
                last_date = calendar_dates[-1]
                
                # 如果请求的日期不在API返回的日期范围内
                if date_str < first_date or date_str > last_date:
                    # 检查请求的月份是否与API返回的月份相同
                    api_month = int(first_date.split('-')[1])
                    api_year = int(first_date.split('-')[0])
                    
                    if year != api_year or month != api_month:
                        # API只返回当前月份数据，无法查询其他月份
                        raise ValueError(f"无法查询{year}年{month}月的数据。深交所API仅支持查询当前月份({api_year}年{api_month}月)的交易日信息")
                    else:
                        # 日期在请求的月份内，但不在API返回的数据中
                        raise ValueError(f"无法找到日期 {date_str} 的交易信息。API返回的{year}年{month}月日期范围是{first_date}到{last_date}")
            else:
                # API返回的数据为空
                raise ValueError(f"无法查询{year}年{month}月的数据。API返回的数据为空")
        
        # 理论上不会到达这里，但为了保险起见
        return False
    
    def get_next_trading_day(self, date):
        """
        获取下一个交易日
        
        :param date: 日期对象或字符串（格式如'2026-01-01'）
        :return: 下一个交易日的日期对象
        """
        # 处理日期参数
        if isinstance(date, str):
            current_date = datetime.strptime(date, '%Y-%m-%d')
        else:
            current_date = date
        
        # 最多查询30天
        for i in range(1, 31):
            next_date = current_date + timedelta(days=i)
            if self.is_trading_day(next_date):
                return next_date
        
        raise ValueError("无法在30天内找到下一个交易日")
    
    def get_previous_trading_day(self, date):
        """
        获取上一个交易日
        
        :param date: 日期对象或字符串（格式如'2026-01-01'）
        :return: 上一个交易日的日期对象
        """
        # 处理日期参数
        if isinstance(date, str):
            current_date = datetime.strptime(date, '%Y-%m-%d')
        else:
            current_date = date
        
        # 最多查询30天
        for i in range(1, 31):
            prev_date = current_date - timedelta(days=i)
            if self.is_trading_day(prev_date):
                return prev_date
        
        raise ValueError("无法在30天内找到上一个交易日")
    
    def get_trading_days_in_month(self, year, month):
        """
        获取指定月份的所有交易日
        
        :param year: 年份
        :param month: 月份
        :return: 交易日日期对象列表
        """
        calendar_data = self.get_month_calendar(year, month)
        trading_days = []
        
        for day in calendar_data.get('data', []):
            if day['jybz'] == '1':
                date_obj = datetime.strptime(day['jyrq'], '%Y-%m-%d')
                trading_days.append(date_obj)
        
        return trading_days
    
    def get_trading_days_between(self, start_date, end_date):
        """
        获取指定日期范围内的所有交易日
        
        :param start_date: 开始日期（对象或字符串）
        :param end_date: 结束日期（对象或字符串）
        :return: 交易日日期对象列表
        """
        # 处理日期参数
        if isinstance(start_date, str):
            start = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start = start_date
            
        if isinstance(end_date, str):
            end = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end = end_date
        
        # 确保开始日期早于结束日期
        if start > end:
            start, end = end, start
        
        trading_days = []
        current = start
        
        # 遍历日期范围
        while current <= end:
            if self.is_trading_day(current):
                trading_days.append(current)
            current += timedelta(days=1)
        
        return trading_days