import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { GuestPortal } from './GuestPortal';
import { guestPortalApi } from '../../services/api';

vi.mock('../../services/api', () => ({
  isDemoMode: () => true,
  guestPortalApi: {
    read: vi.fn(),
    submit: vi.fn(),
  },
  musicSuggestionsApi: {
    createPublic: vi.fn(),
  },
}));

const context = {
  event: { id: 1, name: 'Casamento Teste', date: '2026-09-19', location: 'Espaço Aurora' },
  invitation: {
    tenant_id: 1,
    event_id: 1,
    guest_id: 10,
    type: 'family' as const,
    label: 'Família Teste',
    members: [
      { id: 10, name: 'Ana Teste', category: 'Família', status: 'pending' as const },
      { id: 11, name: 'João Teste', category: 'Família', status: 'pending' as const },
    ],
  },
  response: {},
  playlist: null,
};

describe('GuestPortal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.pushState({}, '', '/guest/token-de-integracao');
    vi.mocked(guestPortalApi.read).mockResolvedValue(context);
    vi.mocked(guestPortalApi.submit).mockResolvedValue({
      members: [
        { id: 10, status: 'confirmed' },
        { id: 11, status: 'pending' },
      ],
    });
  });

  it('loads invitation data and persists member responses', async () => {
    render(<GuestPortal />);

    expect(await screen.findByText('Casamento Teste')).toBeInTheDocument();
    expect(screen.getByText('Ana Teste')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Presença de Ana Teste'), {
      target: { value: 'confirmed' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Enviar resposta' }));

    await waitFor(() => expect(guestPortalApi.submit).toHaveBeenCalledWith(
      'token-de-integracao',
      expect.objectContaining({
        members: expect.arrayContaining([{ guest_id: 10, status: 'confirmed' }]),
      }),
    ));
    expect(await screen.findByText('Resposta enviada')).toBeInTheDocument();
  });

  it('runs the portfolio invitation without a backend', async () => {
    window.history.pushState({}, '', '/guest/lumyra-demo-invitation-token');

    render(<GuestPortal />);

    expect(await screen.findByText('Casamento Ana & João')).toBeInTheDocument();
    expect(screen.getByText(/nenhuma informação será enviada/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Enviar resposta' }));

    expect(await screen.findByText('Resposta enviada')).toBeInTheDocument();
    expect(guestPortalApi.read).not.toHaveBeenCalled();
    expect(guestPortalApi.submit).not.toHaveBeenCalled();
  });
});
