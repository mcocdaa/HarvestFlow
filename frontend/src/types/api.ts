/** API 统一响应包装类型 */

/**
 * 成功响应包装（对应后端 api/v1/common.py 的 ok() 辅助）。
 * 后端响应形状多样（{success, session} / {sessions, total} / {plugins} 等），
 * 此处仅标注 success 字段，具体负载用索引签名 + 页面内显式收窄：
 *
 *   const plugins = (res.data.plugins as Plugin[] | undefined) ?? [];
 */
export interface ApiResponse {
  success: boolean;
  [key: string]: unknown;
}

/** 列表响应：常见的 { items: T[]; total } 结构 */
export interface ListResponse<T> {
  items?: T[];
  total?: number;
  [key: string]: unknown;
}

/** 后端错误 detail：字符串或 pydantic 校验错误对象数组（由拦截器统一展示） */
export type ErrorDetail = string | Array<{ msg?: string; [key: string]: unknown }>;
