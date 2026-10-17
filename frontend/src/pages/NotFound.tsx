import React from 'react';
import { Button, Result } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '../i18n';

const NotFound: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useI18n();

  return (
    <Result
      status="404"
      title="404"
      subTitle={t('抱歉，您访问的页面不存在', 'Sorry, the page you visited does not exist.')}
      extra={
        <Button type="primary" onClick={() => navigate('/')}>
          {t('返回首页', 'Back to Home')}
        </Button>
      }
    />
  );
};

export default NotFound;
