import { message } from 'antd';
import { getStoredLocale } from '../i18n';

export const copyToClipboard = async (
  text: string,
  successMessage = getStoredLocale() === 'zh' ? '已复制到剪贴板' : 'Copied to clipboard'
): Promise<void> => {
  try {
    await navigator.clipboard.writeText(text);
    message.success(successMessage);
  } catch {
    message.error(getStoredLocale() === 'zh' ? '复制失败' : 'Copy failed');
  }
};
