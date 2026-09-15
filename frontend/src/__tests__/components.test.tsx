import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ScoreTag, StatusTag } from '../components';

describe('StatusTag', () => {
  it('should render Chinese labels for all statuses', () => {
    render(
      <>
        <StatusTag status="raw" />
        <StatusTag status="curated" />
        <StatusTag status="approved" />
        <StatusTag status="rejected" />
      </>
    );

    expect(screen.getByText('待清洗')).toBeInTheDocument();
    expect(screen.getByText('待审核')).toBeInTheDocument();
    expect(screen.getByText('已通过')).toBeInTheDocument();
    expect(screen.getByText('已拒绝')).toBeInTheDocument();
  });

  it('should fall back for unknown status', () => {
    render(<StatusTag status="unknown-status" />);
    expect(screen.getByText('unknown-status')).toBeInTheDocument();
  });
});

describe('ScoreTag', () => {
  it('should render dash when score is missing', () => {
    render(<ScoreTag score={null} />);
    expect(screen.getByText('-')).toBeInTheDocument();
  });

  it('should render score value', () => {
    render(<ScoreTag score={4} />);
    expect(screen.getByText('4')).toBeInTheDocument();
  });

  it('should render label variant', () => {
    render(<ScoreTag score={4} showLabel />);
    expect(screen.getByText('优 · 良好')).toBeInTheDocument();
  });
});
