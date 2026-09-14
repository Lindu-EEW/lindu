import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import AlarmBanner from './AlarmBanner';

// Mock getDistance internally in the test since it's inside the component
describe('AlarmBanner Component', () => {
  const mockLiveAlarm = {
    epi_lat: -6.8222,
    epi_lon: 107.1388,
    radius_km: 50.0,
    timestamp: Date.now(),
    desc: "Gempa Bumi Test",
    magnitude: 6.0
  };

  it('renders nothing when there is no alarm', () => {
    const { container } = render(<AlarmBanner liveAlarm={null} userLat={0} userLon={0} onDismiss={() => {}} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when the user is outside the radius (Safe)', () => {
    // User in Tokyo, Earthquake in Indonesia
    const { container } = render(
      <AlarmBanner 
        liveAlarm={mockLiveAlarm} 
        userLat={35.6895} 
        userLon={139.6917} 
        onDismiss={() => {}} 
      />
    );
    // Since we removed the safe popup earlier, it should return null
    expect(container.firstChild).toBeNull();
  });
});
