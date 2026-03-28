// @file plugins/examples/reviewer-example/frontend.tsx
// @brief Example reviewer plugin frontend component
// @create 2026-03-28

import React from 'react';
import { Form, Select, Input, Checkbox, Card } from 'antd';

const { Option } = Select;
const { TextArea } = Input;

interface ReviewerExtraFieldsProps {
  values: any;
  onChange: (values: any) => void;
}

export const ReviewerExtraFields: React.FC<ReviewerExtraFieldsProps> = ({ values, onChange }) => {
  const [form] = Form.useForm();

  React.useEffect(() => {
    form.setFieldsValue(values);
  }, [values, form]);

  const handleValuesChange = (changedValues: any, allValues: any) => {
    onChange(allValues);
  };

  return (
    <Card size="small" title="扩展字段" style={{ marginTop: 16 }}>
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChange}
        initialValues={values}
      >
        <Form.Item name="data_quality" label="数据质量">
          <Select placeholder="请选择数据质量">
            <Option value="优秀">优秀</Option>
            <Option value="良好">良好</Option>
            <Option value="一般">一般</Option>
            <Option value="较差">较差</Option>
          </Select>
        </Form.Item>

        <Form.Item name="use_case" label="使用场景">
          <TextArea
            rows={2}
            placeholder="请输入该会话的使用场景"
            showCount
            maxLength={200}
          />
        </Form.Item>

        <Form.Item name="needs_review" valuePropName="checked">
          <Checkbox>需要复查</Checkbox>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default {
  name: 'reviewer-example',
  ExtraFieldsComponent: ReviewerExtraFields,
};
