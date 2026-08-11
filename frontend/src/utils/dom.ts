/** 判断事件目标是否为可编辑元素（输入框/文本域/按钮/可编辑容器） */
export const isEditableTarget = (target: EventTarget | null): boolean => {
  const el = target as HTMLElement | null;
  if (!el?.tagName) return false;
  const tagName = el.tagName.toLowerCase();
  return (
    tagName === 'input' ||
    tagName === 'textarea' ||
    tagName === 'button' ||
    el.isContentEditable ||
    el.contentEditable === 'true'
  );
};
