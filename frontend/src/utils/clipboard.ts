import { message } from 'antd';

export const copyToClipboard = async (text: string, successMessage = '已复制到剪贴板'): Promise<void> => {
  try {
    await navigator.clipboard.writeText(text);
    message.success(successMessage);
  } catch (error) {
    message.error('复制失败');
  }
};
