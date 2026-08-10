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

  it('should render object content as JSON.stringify', () => {
    const message: Message = {
      role: 'assistant',
      content: { tool_calls: [{ name: 'read_file', args: { path: '/test' } }] },
    }

    render(<MessageBubble message={message} index={1} />)

    // Should show JSON representation
    expect(screen.getByText(/"tool_calls"/)).toBeInTheDocument()
    expect(screen.getByText(/"read_file"/)).toBeInTheDocument()
  })

  it('should display "用户" label for user role', () => {
    const message: Message = {
      role: 'user',
      content: 'test',
    }

    render(<MessageBubble message={message} index={0} />)

    expect(screen.getByText('用户')).toBeInTheDocument()
  })

  it('should display "AI" label for assistant role', () => {
    const message: Message = {
      role: 'assistant',
      content: 'response',
    }

    render(<MessageBubble message={message} index={0} />)

    expect(screen.getByText('AI')).toBeInTheDocument()
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

  it('should render avatar emoji for user', () => {
    const message: Message = {
      role: 'user',
      content: 'test',
    }

    render(<MessageBubble message={message} index={0} />)

    expect(screen.getByText('👤')).toBeInTheDocument()
  })

  it('should render avatar emoji for AI', () => {
    const message: Message = {
      role: 'assistant',
      content: 'test',
    }

    render(<MessageBubble message={message} index={0} />)

    expect(screen.getByText('🤖')).toBeInTheDocument()
  })
})
