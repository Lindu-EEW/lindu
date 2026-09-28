import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import HistorySidebar from './HistorySidebar';

describe('HistorySidebar Component', () => {
  it('renders nodes without crashing when lat and lon are undefined', () => {
    const mockNodes = {
      'node_test': {
        id: 'node_test',
        status: 'online',
        // lat and lon are missing/undefined
      }
    };

    render(
      <HistorySidebar
        history={[]}
        activeNodes={mockNodes}
        onSelectQuake={() => {}}
        onFocusNode={() => {}}
        onOpenDetail={() => {}}
      />
    );

    // Switch to sensors tab
    fireEvent.click(screen.getByText('Stasiun Sensor'));

    expect(screen.getByText('Sensor: node_test')).toBeTruthy();
    expect(screen.getByText('Posisi: Koordinat tidak tersedia')).toBeTruthy();
  });

  it('renders formatted coordinates when lat and lon are present', () => {
    const mockNodes = {
      'node_ok': {
        id: 'node_ok',
        lat: 35.5402,
        lon: 139.5178,
      }
    };

    render(
      <HistorySidebar
        history={[]}
        activeNodes={mockNodes}
        onSelectQuake={() => {}}
        onFocusNode={() => {}}
        onOpenDetail={() => {}}
      />
    );

    // Switch to sensors tab
    fireEvent.click(screen.getByText('Stasiun Sensor'));

    expect(screen.getByText('Sensor: node_ok')).toBeTruthy();
    expect(screen.getByText('Posisi: 35.5402, 139.5178')).toBeTruthy();
  });
});
