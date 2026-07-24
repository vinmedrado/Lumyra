import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { demoActions, getDemoStats, useDemoStore } from './demoStore';

describe('portfolio demo store', () => {
  beforeEach(() => {
    demoActions.reset();
  });

  it('shares RSVP updates with every persona and records the action', () => {
    const { result } = renderHook(() => useDemoStore());

    act(() => {
      demoActions.submitFamilyRsvp({
        members: [
          { guestId: 101, status: 'confirmed' },
          { guestId: 102, status: 'declined' },
          { guestId: 103, status: 'confirmed' },
        ],
        phone: '(11) 90000-0101',
        needsBus: true,
        dietary: 'Sem lactose',
      });
    });

    expect(result.current.guests.find(guest => guest.id === 101)).toMatchObject({
      status: 'confirmed',
      phone: '(11) 90000-0101',
      needsBus: true,
      dietary: 'Sem lactose',
    });
    expect(getDemoStats(result.current)).toMatchObject({ confirmed: 10, declined: 3, pending: 2 });
    expect(result.current.activity[0].actor).toBe('Portal do convidado');
    expect(result.current.notifications[0].title).toBe('Novo RSVP recebido');
  });

  it('propagates financial and music curation changes', () => {
    const { result } = renderHook(() => useDemoStore());

    act(() => {
      demoActions.toggleExpensePaid(3);
      demoActions.addMusicSuggestion('Marina Oliveira', 'Trevo', 'ANAVITÓRIA', 'Para a pista.');
    });

    const suggestion = result.current.musicSuggestions[0];
    expect(result.current.expenses.find(expense => expense.id === 3)?.paid).toBe(true);
    expect(suggestion).toMatchObject({ song: 'Trevo', status: 'pending' });

    act(() => demoActions.updateMusicSuggestionStatus(suggestion.id, 'approved'));
    expect(result.current.musicSuggestions[0].status).toBe('approved');
  });
});
