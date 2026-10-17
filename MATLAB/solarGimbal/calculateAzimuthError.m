function [azimuthError, direction] = calculateAzimuthError(sunAzimuth, panelAzimuth)
% CALCULATEAZIMUTHERROR Calculates normalized azimuth error with 360-degree wrap-around.
%
% Mathematical Formula:
%   error = mod(sun_azimuth - panel_azimuth + 180, 360) - 180
%
% Wrap-around Verification:
%   sun_azimuth = 5 deg, panel_azimuth = 355 deg:
%     raw diff = -350 deg
%     mod(-350 + 180, 360) - 180 = mod(-170, 360) - 180 = 190 - 180 = +10 deg
%     Direction: CLOCKWISE
%
% Direction Determination:
%   error > 0  => "CLOCKWISE"
%   error < 0  => "COUNTER_CLOCKWISE"
%   error == 0 => "HOLD"
%
% Hardware Mapping:
%   In FPGA fixed-point arithmetic, signed modular reduction is implemented
%   using standard two's-complement overflow truncation without division.

    if nargin < 2
        error('calculateAzimuthError:InsufficientArgs', 'Both sunAzimuth and panelAzimuth are required.');
    end

    sAz = double(sunAzimuth);
    pAz = double(panelAzimuth);

    % Normalized angular error in range [-180, 180)
    azimuthError = mod(sAz - pAz + 180.0, 360.0) - 180.0;

    % Direction classification
    if azimuthError > 1e-6
        direction = "CLOCKWISE";
    elseif azimuthError < -1e-6
        direction = "COUNTER_CLOCKWISE";
    else
        azimuthError = 0.0;
        direction = "HOLD";
    end
end
