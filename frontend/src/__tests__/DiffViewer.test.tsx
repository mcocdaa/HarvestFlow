import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import DiffViewer from '../components/review/DiffViewer';

describe('DiffViewer Component', () => {
  it('should render diff lines showing removals and additions', () => {
    const orig = 'def hello():\n    print("bad")';
    const mod = 'def hello():\n    print("good")';

    render(<DiffViewer original={orig} modified={mod} />);

    expect(screen.getByText('修改前后对比 Diff (DPO 偏好对)')).toBeInTheDocument();
    expect(screen.getByText('-1 删减')).toBeInTheDocument();
    expect(screen.getByText('+1 新增')).toBeInTheDocument();
  });

  it('should handle identical text without changes', () => {
    const text = 'identical content';
    render(<DiffViewer original={text} modified={text} />);

    expect(screen.getByText('+0 新增')).toBeInTheDocument();
    expect(screen.getByText('-0 删减')).toBeInTheDocument();
  });
});
