function movement = calculateMovement(azimuthError, elevationError, Kp)
% CALCULATEMOVEMENT Calculates required angular gimbal movements and control efforts.
%
% Direct Tracking:
%   required_azimuth_movement = normalized_azimuth_error
%   required_elevation_movement = elevation_error
%
% Optional Proportional Control Model:
%   control_output_azimuth = Kp * azimuth_error
%   control_output_elevation = Kp * elevation_error
%
% Inputs:
%   azimuthError   - Normalized azimuth error in degrees [-180, 180)
%   elevationError - Elevation error in degrees [-180, 180]
%   Kp             - (Optional) Proportional gain (default = 1.0 for direct tracking)
%
% Outputs:
%   movement - struct with fields:
%                .requiredAzimuthMovement
%                .requiredElevationMovement
%                .azimuthDirection
%                .elevationDirection
%                .controlOutputAzimuth
%                .controlOutputElevation

    if nargin < 3 || isempty(Kp)
        Kp = 1.0; % Default: Direct angular-error tracking
    else
        Kp = double(Kp);
    end

    azErr = double(azimuthError);
    elErr = double(elevationError);

    % Required physical movements in degrees
    reqAz = azErr;
    reqEl = elErr;

    % Optional proportional control effort
    ctrlAz = Kp * azErr;
    ctrlEl = Kp * elErr;

    % Directions
    if reqAz > 1e-6
        azDir = "CLOCKWISE";
    elseif reqAz < -1e-6
        azDir = "COUNTER_CLOCKWISE";
    else
        azDir = "HOLD";
    end

    if reqEl > 1e-6
        elDir = "UP";
    elseif reqEl < -1e-6
        elDir = "DOWN";
    else
        elDir = "HOLD";
    end

    movement = struct( ...
        'requiredAzimuthMovement', reqAz, ...
        'requiredElevationMovement', reqEl, ...
        'azimuthDirection', azDir, ...
        'elevationDirection', elDir, ...
        'controlOutputAzimuth', ctrlAz, ...
        'controlOutputElevation', ctrlEl, ...
        'Kp', Kp);
end
