/**
 * 格式化日期
 */
export function formatDate(
  date: Date | number | string,
  format: 'full' | 'short' | 'time' | 'relative' = 'short'
): string {
  const d = typeof date === 'number' || typeof date === 'string' ? new Date(date) : date;

  switch (format) {
    case 'full':
      return d.toLocaleString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });

    case 'short':
      return d.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });

    case 'time':
      return d.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      });

    case 'relative':
      return formatRelativeTime(d);

    default:
      return d.toLocaleString('zh-CN');
  }
}

/**
 * 格式化相对时间
 */
export function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 7) return `${days}天前`;

  return formatDate(date, 'short');
}

/**
 * 获取今日日期
 */
export function getToday(): Date {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return now;
}

/**
 * 判断是否是今天
 */
export function isToday(date: Date | number | string): boolean {
  const d = typeof date === 'number' || typeof date === 'string' ? new Date(date) : date;
  const today = getToday();
  const target = new Date(d);
  target.setHours(0, 0, 0, 0);
  return today.getTime() === target.getTime();
}

/**
 * 获取时间戳
 */
export function getTimestamp(): number {
  return Date.now();
}
