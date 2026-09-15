import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MessageBubble from '../components/common/MessageBubble'
import type { Message } from '../types'

describe('MessageBubble Component', () => {
  it('should render string content directly', () => {
    const message: Message = {
      role: 'user',
      content: 'Hello, how can I help?',
    }

    render(<MessageBubble message={message} index={0} />)

    expect(screen.getByText('Hello, how can I help?')).toBeInTheDocument()
  })

  it('should render object content as JSON', () => {
    const message: Message = {
      role: 'assistant',
      content: { tool_calls: [{ name: 'read_file', args: { path: '/test' } }] },
    }

    render(<MessageBubble message={message} index={1} />)

    expect(screen.getByText(/"tool_calls"/)).toBeInTheDocument()
    expect(screen.getByText(/"read_file"/)).toBeInTheDocument()
  })

  it('should display 用户 label for user role', () => {
    const message: Message = {
      role: 'user',
      content: 'test',
    }

    render(<MessageBubble message={message} index={0} />)

    expect(screen.getByText('用户')).toBeInTheDocument()
  })

  it('should display AI 助手 label for assistant role', () => {
    const message: Message = {
      role: 'assistant',
      content: 'response',
    }

    render(<MessageBubble message={message} index={0} />)

    expect(screen.getByText('AI 助手')).toBeInTheDocument()
  })

  it('should display 系统 label for system role', () => {
    const message: Message = {
      role: 'system',
      content: 'system prompt',
    }

    render(<MessageBubble message={message} index={0} />)

    expect(screen.getByText('系统')).toBeInTheDocument()
  })

  it('should display correct message index', () => {
    const message: Message = {
      role: 'user',
      content: 'test',
    }

    render(<MessageBubble message={message} index={3} />)

    expect(screen.getByText('#4')).toBeInTheDocument()
  })

  it('should apply role-based className', () => {
    const message: Message = {
      role: 'assistant',
      content: 'test',
    }

    const { container } = render(<MessageBubble message={message} index={0} />)

    const bubble = container.querySelector('.message-bubble')
    expect(bubble).toBeInTheDocument()
    expect(bubble?.classList.contains('assistant')).toBe(true)
  })

  it('should render SVG role avatar instead of emoji', () => {
    const message: Message = {
      role: 'user',
      content: 'test',
    }

    const { container } = render(<MessageBubble message={message} index={0} />)

    const avatar = container.querySelector('.bubble-avatar')
    expect(avatar).toBeInTheDocument()
    expect(avatar?.querySelector('svg')).toBeInTheDocument()
    // 不允许出现 emoji 头像
    expect(avatar?.textContent).toBe('')
  })

  it('should render tool call tags', () => {
    const message: Message = {
      role: 'assistant',
      content: 'done',
      tool_calls: [{ type: 'tool_use', name: 'read_file' }],
    }

    render(<MessageBubble message={message} index={0} />)

    expect(screen.getByText('read_file')).toBeInTheDocument()
  })
})
