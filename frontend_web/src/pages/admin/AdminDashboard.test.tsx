import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AdminDashboard } from './AdminDashboard';
import { analyticsApi, eventsApi, insightsApi } from '../../services/api';

vi.mock('../../services/api', () => ({
  hasStoredAccessToken: () => true,
  eventsApi: { list: vi.fn() },
  analyticsApi: { overview: vi.fn() },
  insightsApi: { list: vi.fn() },
}));

describe('AdminDashboard', () => {
  beforeEach(() => {
    vi.mocked(eventsApi.list).mockResolvedValue([{ id: 7, name: 'Evento API' }]);
    vi.mocked(analyticsApi.overview).mockResolvedValue({
      total_guests: 120,
      confirmed: 90,
      pending: 20,
      declined: 10,
      confirmation_rate: 75,
      campaign_response_rate: 90,
      message_errors: 2,
      table_occupancy: [{ table_name: 'Mesa 1', occupied: 8 }],
      financial: { contracted: 100000, paid: 60000 },
    });
    vi.mocked(insightsApi.list).mockResolvedValue([
      { severity: 'warning', title: 'RSVP pendente', message: '20 pendências' },
    ]);
  });

  it('renders metrics returned by the API', async () => {
    render(<AdminDashboard />);

    expect(await screen.findByText('Evento API')).toBeInTheDocument();
    expect(screen.getByText('120')).toBeInTheDocument();
    expect(screen.getByText('90')).toBeInTheDocument();
    expect(screen.getByText('RSVP pendente')).toBeInTheDocument();
  });
});
