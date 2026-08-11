import { describe, it, expect } from 'vitest'
import { isEditableTarget } from '../utils'

describe('isEditableTarget', () => {
  it('returns true for input elements', () => {
    const el = document.createElement('input')
    expect(isEditableTarget(el)).toBe(true)
  })

  it('returns true for textarea elements', () => {
    const el = document.createElement('textarea')
    expect(isEditableTarget(el)).toBe(true)
  })

  it('returns true for button elements', () => {
    const el = document.createElement('button')
    expect(isEditableTarget(el)).toBe(true)
  })

  it('returns true for contentEditable elements', () => {
    const el = document.createElement('div')
    el.contentEditable = 'true'
    expect(isEditableTarget(el)).toBe(true)
  })

  it('returns false for plain div', () => {
    const el = document.createElement('div')
    expect(isEditableTarget(el)).toBe(false)
  })

  it('returns false for body', () => {
    expect(isEditableTarget(document.body)).toBe(false)
  })

  it('returns false for null', () => {
    expect(isEditableTarget(null)).toBe(false)
  })
})
