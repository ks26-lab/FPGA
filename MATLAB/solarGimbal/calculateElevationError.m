function [elevationError, direction] = calculateElevationError(sunElevation, panelElevation)
% CALCULATEELEVATIONERROR Calculates angular elevation error.
%
% Formula:
%   elevation_error = sun_elevation - panel_elevation
%
% Direction Determination:
%   error > 0  => "UP"
%   error < 0  => "DOWN"
%   error == 0 => "HOLD"

    if nargin < 2
        error('calculateElevationError:InsufficientArgs', 'Both sunElevation and panelElevation are required.');
    end

    sEl = double(sunElevation);
    pEl = double(panelElevation);

    elevationError = sEl - pEl;

    if elevationError > 1e-6
        direction = "UP";
    elseif elevationError < -1e-6
        direction = "DOWN";
    else
        elevationError = 0.0;
        direction = "HOLD";
    end
end
